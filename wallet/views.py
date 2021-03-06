# -*- coding: utf8 -*-
from django.utils.timezone import now

from rest_framework import generics
from rest_framework.response import Response
from rest_framework import status
from wallet.serializers import (WalletSerializer,
                                WalletDetailListSerializer,
                                WalletResponseSerializer,
                                WithdrawSerializer,
                                BankCardSerializer,
                                BankCardListSerializer,
                                WithdrawRecordListSerializer)
from wallet.permissions import IsOwnerOrReadOnly, IsAdminOrReadOnly
from wallet.models import (Wallet,
                           WalletTradeDetail,
                           WithdrawRecord,
                           BankCard,
                           WITHDRAW_ACTION_ISO_WEEKDAY)
from wallet.forms import (WalletDetailListForm,
                          WalletCreateForm,
                          WithdrawActionForm,
                          BankCardAddForm,
                          BankCardDeleteForm,
                          WithdrawRecordListForm,
                          WithdrawUpdateForm)
from users.caches import BusinessUserCache

import re


class WalletAction(generics.GenericAPIView):
    """
    钱包相关功能
    """
    permission_classes = (IsOwnerOrReadOnly, )

    def get_wallet_object(self, request):
        return Wallet.get_object(user_id=request.user.id)

    def post(self, request, *args, **kwargs):
        """
        创建用户钱包
        """
        form = WalletCreateForm(request.data)
        if not form.is_valid():
            return Response({'Detail': form.errors}, status=status.HTTP_400_BAD_REQUEST)

        cld = form.cleaned_data
        wallet = self.get_wallet_object(request)
        if not isinstance(wallet, Exception):
            serializer_res = WalletResponseSerializer(wallet)
            return Response(serializer_res.data, status=status.HTTP_400_BAD_REQUEST)

        serializer = WalletSerializer(data=cld, request=request)
        if not serializer.is_valid():
            return Response({'Detail': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        try:
            serializer.save()
        except Exception as e:
            return Response({'Detail': e.args}, status=status.HTTP_400_BAD_REQUEST)
        serializer_res = WalletResponseSerializer(data=serializer.data)
        if not serializer_res.is_valid():
            return Response({'Detail': serializer_res.errors}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer_res.data, status=status.HTTP_201_CREATED)


class WalletDetail(generics.GenericAPIView):
    """
    钱包余额
    """
    permission_classes = (IsOwnerOrReadOnly, )

    def get_wallet_info(self, request):
        _wallet = Wallet.get_object(**{'user_id': request.user.id})
        if isinstance(_wallet, Exception):
            initial_dict = {'user_id': request.user.id,
                            'balance': '0'}
            _wallet = Wallet(**initial_dict)
        return _wallet

    def get(self, request, *args, **kwargs):
        """
        展示用户钱包余额
        """
        _instance = self.get_wallet_info(request)
        serializer = WalletResponseSerializer(_instance)
        return Response(serializer.data, status=status.HTTP_200_OK)


class WalletTradeDetailList(generics.GenericAPIView):
    """
    钱包明细
    """
    permission_classes = (IsOwnerOrReadOnly, )

    def get_details_list(self, request, cld):
        kwargs = {'user_id': request.user.id}
        kwargs.update(**cld)
        return WalletTradeDetail.get_success_list(**kwargs)

    def post(self, request, *args, **kwargs):
        form = WalletDetailListForm(request.data)
        if not form.is_valid():
            return Response({'Detail': form.errors}, status=status.HTTP_400_BAD_REQUEST)

        cld = form.cleaned_data
        _instances = self.get_details_list(request, cld)
        if isinstance(_instances, Exception):
            return Response({'Detail': _instances.args}, status=status.HTTP_400_BAD_REQUEST)
        serializer = WalletDetailListSerializer(_instances)
        result = serializer.list_data(**cld)
        if isinstance(result, Exception):
            return Response({'Detail': result.args}, status=status.HTTP_400_BAD_REQUEST)
        return Response(result, status=status.HTTP_200_OK)


class WithdrawAction(generics.GenericAPIView):
    """
    钱包提现
    """
    permission_classes = (IsOwnerOrReadOnly,)

    def has_enough_balance(self, request, amount_of_money):
        """
        余额是否充足
        """
        if not Wallet.can_withdraw(request):
            return False
        return Wallet.has_enough_balance(request, amount_of_money)

    def is_bank_card_valid(self, request, account_id):
        instance = BankCard.get_object(pk=account_id)
        if isinstance(instance, Exception):
            return False
        if instance.user_id != request.user.id:
            return False
        return True

    def get_bank_card_instance(self, account_id):
        return BankCard.get_object(pk=account_id)

    def get_withdraw_recode(self, pk):
        return WithdrawRecord.get_unpaid_object(pk=pk)

    def is_request_data_valid(self, request):
        current_time = now()
        if current_time.isoweekday() not in WITHDRAW_ACTION_ISO_WEEKDAY:
            return False, Exception('Withdraw operate must in weekday'
                                    ' %s' % list(WITHDRAW_ACTION_ISO_WEEKDAY))

        form = WithdrawActionForm(request.data)
        if not form.is_valid():
            return False, Exception(form.errors)

        cld = form.cleaned_data
        try:
            float(cld['amount_of_money'])
        except Exception as e:
            return False, e
        if float(cld['amount_of_money']) <= 0:
            return False, ValueError('Fields [amount_of_money]: data is incorrect')

        # 判断银行账户是否存在及是否属于本人
        if not self.is_bank_card_valid(request, cld['account_id']):
            return False, Exception('Permission denied')
        return True, cld

    def post(self, request, *args, **kwargs):
        """
        提现申请
        """
        bool_res, cld = self.is_request_data_valid(request)
        if not bool_res:
            return Response({'Detail': cld.args}, status=status.HTTP_400_BAD_REQUEST)

        amount_of_money = cld['amount_of_money']
        has_enough = self.has_enough_balance(request, amount_of_money)
        if not has_enough:
            return Response({'Detail': 'Your balance is not enough.'},
                            status=status.HTTP_400_BAD_REQUEST)

        serializer = WithdrawSerializer(data=cld, request=request)
        if serializer.is_valid():
            result = serializer.save(request, amount_of_money)
            if isinstance(result, Exception):
                return Response({'Detail': result.args}, status=status.HTTP_400_BAD_REQUEST)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response({'Detail': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, *args, **kwargs):
        """
        提现审核结果
        """
        if not request.user.is_admin:
            return Response({'Detail': 'Permission denied'}, status=status.HTTP_400_BAD_REQUEST)

        form = WithdrawUpdateForm(request.data)
        if not form.is_valid():
            return Response({'Detail': form.errors}, status=status.HTTP_400_BAD_REQUEST)
        cld = form.cleaned_data
        with_status = int(cld['status'])
        instance = self.get_withdraw_recode(cld['pk'])
        if isinstance(instance, Exception):
            return Response({'Detail': instance.args}, status=status.HTTP_400_BAD_REQUEST)

        serializer = WithdrawSerializer(instance)
        with_instance = serializer.update_status(request, instance, {'status': with_status})
        if isinstance(with_instance, Exception):
            return Response({'Detail': with_instance.args}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.data, status=status.HTTP_206_PARTIAL_CONTENT)


class WithdrawRecordList(generics.GenericAPIView):
    permission_classes = (IsOwnerOrReadOnly,)

    def get_records(self, request):
        return WithdrawRecord.filter_objects(user_id=request.user.id)

    def post(self, request, *args, **kwargs):
        form = WithdrawRecordListForm(request.data)
        if not form.is_valid():
            return Response({'Detail': form.errors}, status=status.HTTP_400_BAD_REQUEST)

        cld = form.cleaned_data
        instances = self.get_records(request)
        if isinstance(instances, Exception):
            return Response({'Detail': instances.args}, status=status.HTTP_400_BAD_REQUEST)
        serializer = WithdrawRecordListSerializer(instances)
        datas = serializer.list_data(**cld)
        if isinstance(datas, Exception):
            return Response({'Detail': datas.args}, status=status.HTTP_400_BAD_REQUEST)
        return Response(datas, status=status.HTTP_200_OK)


class BankCardAction(generics.GenericAPIView):
    """
    银行卡绑定或解除绑定 (需要管理员权限)
    """
    permission_classes = (IsAdminOrReadOnly,)

    def does_user_exist(self, request, user_id):
        ins = BusinessUserCache().get_user_by_id(request, user_id)
        if isinstance(ins, Exception):
            return False
        return True

    def get_bank_card_instance(self, pk):
        return BankCard.get_object(pk=pk)

    def get_perfect_card_number(self, bank_card_number):
        re_com = re.compile(r'^[0-9]+$')
        card_num_list = bank_card_number.split()
        card_num_str = ''.join(card_num_list)
        for item in card_num_list:
            if not re_com.match(item):
                return ValueError('Bank card number is incorrect.')
        if len(card_num_str) > 20:
            return ValueError('Bank card number is incorrect.')

        perfect_list = []
        for index in range(len(card_num_str) / 4 + 1):
            if index * 4 < len(card_num_str):
                perfect_list.append(card_num_str[index * 4: index * 4 + 4])
        return ' '.join(perfect_list)

    def post(self, request, *args, **kwargs):
        """
        绑定银行卡
        """
        form = BankCardAddForm(request.data)
        if not form.is_valid():
            return Response({'Detail': form.errors}, status=status.HTTP_400_BAD_REQUEST)

        cld = form.cleaned_data
        if not self.does_user_exist(request, cld['user_id']):
            return Response({'Detail': 'The user %d does exist.' % cld['user_id']},
                            status=status.HTTP_400_BAD_REQUEST)

        bank_card_number = self.get_perfect_card_number(cld['bank_card_number'])
        if isinstance(bank_card_number, Exception):
            return Response({'Detail': bank_card_number.args}, status=status.HTTP_400_BAD_REQUEST)

        cld['bank_card_number'] = bank_card_number
        serializer = BankCardSerializer(data=cld)
        if serializer.is_valid():
            result = serializer.save(request)
            if isinstance(result, Exception):
                return Response({'Detail': result.args}, status=status.HTTP_400_BAD_REQUEST)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response({'Detail': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        """
        解除绑定银行卡
        """
        form = BankCardDeleteForm(request.data)
        if not form.is_valid():
            return Response({'Detail': form.errors}, status=status.HTTP_400_BAD_REQUEST)

        cld = form.cleaned_data
        instance = self.get_bank_card_instance(cld['pk'])
        if isinstance(instance, Exception):
            return Response({'Detail': 'The bank card %d does not exist.' % cld['pk']},
                            status=status.HTTP_400_BAD_REQUEST)
        serializer = BankCardSerializer(instance)
        result = serializer.delete(request, instance)
        if isinstance(request, Exception):
            return Response({'Detail': result.args}, status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_204_NO_CONTENT)


class BankCardList(generics.GenericAPIView):
    """
    获取绑定银行卡信息列表
    """
    permission_classes = (IsOwnerOrReadOnly,)

    def get_bank_card_list(self, request):
        return BankCard.filter_perfect_details(request, user_id=request.user.id)

    def get(self, request, *args, **kwargs):
        # form = BankCardListForm(request.data)
        # if not form.is_valid():
        #     return Response({'Detail': form.errors}, status=status.HTTP_400_BAD_REQUEST)
        #
        # cld = form.cleaned_data
        details = self.get_bank_card_list(request)
        if isinstance(details, Exception):
            return Response({'Detail': details.args}, status=status.HTTP_400_BAD_REQUEST)

        serializer = BankCardListSerializer(data=details)
        if not serializer.is_valid():
            return Response({'Detail': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        result = serializer.list_data()
        if isinstance(result, Exception):
            return Response({'Detail': result.args}, status=status.HTTP_400_BAD_REQUEST)
        return Response(result, status=status.HTTP_200_OK)


