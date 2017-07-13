# -*- coding: utf8 -*-
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
                           BankCard)
from wallet.forms import (WalletDetailListForm,
                          WalletCreateForm,
                          WithdrawActionForm,
                          BankCardAddForm,
                          BankCardDeleteForm,
                          WithdrawRecordListForm,
                          WithdrawUpdateForm)
from users.caches import BusinessUserCache


class WalletAction(generics.GenericAPIView):
    """
    钱包相关功能
    """
    permission_classes = (IsOwnerOrReadOnly, )

    def post(self, request, *args, **kwargs):
        """
        创建用户钱包
        """
        form = WalletCreateForm(request.data)
        if not form.is_valid():
            return Response({'Detail': form.errors}, status=status.HTTP_400_BAD_REQUEST)

        cld = form.cleaned_data
        serializer = WalletSerializer(data=cld, _request=request)
        if serializer.is_valid():
            serializer.save()
            serializer_res = WalletResponseSerializer(serializer.data)
            if serializer_res.is_valid():
                return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response({'Detail': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


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

    def post(self, request, *args, **kwargs):
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

    def get_details_list(self, request):
        kwargs = {'user_id': request.user.id}
        return WalletTradeDetail.get_success_list(**kwargs)

    def post(self, request, *args, **kwargs):
        form = WalletDetailListForm(request.data)
        if not form.is_valid():
            return Response({'Detail': form.errors}, status=status.HTTP_400_BAD_REQUEST)

        cld = form.cleaned_data
        _instances = self.get_details_list(request)
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
        return WithdrawRecord.get_object(pk=pk)

    def is_request_data_valid(self, request):
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
            return Response({'Detail': 'Your balance is not enough.'})

        serializer = WithdrawSerializer(data=cld, request=request)
        if serializer.is_valid():
            result = serializer.save(request, amount_of_money)
            if isinstance(result, Exception):
                return Response({'Detail': result.args}, status=status.HTTP_400_BAD_REQUEST)
            return Response(serializer.data, status=status.HTTP_200_OK)
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
        serializer = BankCardSerializer(data=cld)
        if serializer.is_valid():
            result = serializer.save(request)
            if isinstance(result, Exception):
                return Response({'Detail': result.args}, status=status.HTTP_400_BAD_REQUEST)
            return Response(serializer.data, status=status.HTTP_400_BAD_REQUEST)
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
        return BankCard.filter_objects(user_id=request.user.id)

    def post(self, request, *args, **kwargs):
        # form = BankCardListForm(request.data)
        # if not form.is_valid():
        #     return Response({'Detail': form.errors}, status=status.HTTP_400_BAD_REQUEST)
        #
        # cld = form.cleaned_data
        instances = self.get_bank_card_list(request)
        if isinstance(instances, Exception):
            return Response({'Detail': instances.args}, status=status.HTTP_400_BAD_REQUEST)

        serializer = BankCardListSerializer(instances)
        result = serializer.list_data()
        if isinstance(result, Exception):
            return Response({'Detail': result.args}, status=status.HTTP_400_BAD_REQUEST)
        return Response(result, status=status.HTTP_200_OK)


