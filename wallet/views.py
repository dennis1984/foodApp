# -*- coding: utf8 -*-
from rest_framework import generics
from rest_framework.response import Response
from rest_framework import status
from wallet.serializers import (WalletSerializer,
                                WalletDetailListSerializer,
                                WalletResponseSerializer,
                                WithdrawSerializer)
from wallet.permissions import IsOwnerOrReadOnly
from wallet.models import (Wallet,
                           WalletTradeDetail,
                           WithdrawRecord)
from wallet.forms import (WalletDetailListForm,
                          WalletCreateForm,
                          WithdrawActionForm)


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
        return WithdrawRecord(request, amount_of_money)

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
        # ....
        return True, cld

    def post(self, request, *args, **kwargs):
        bool_res, cld = self.is_request_data_valid(request)
        if not bool_res:
            return Response({'Detail': cld.args}, status=status.HTTP_400_BAD_REQUEST)

        amount_of_money = cld['amount_of_money']
        has_enough = self.has_enough_balance(request, amount_of_money)
        if not has_enough:
            return Response({'Detail': 'Your balance is not enough.'})

        serializer = WithdrawSerializer(data=cld, request=request)
        if serializer.is_valid():
            serializer.save(request, amount_of_money)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response({'Detail': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

