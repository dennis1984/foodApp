# -*- coding:utf8 -*-
from django.contrib.auth.hashers import make_password
from wallet.models import (Wallet,
                           WalletTradeDetail,
                           WithdrawRecord,
                           BankCard,
                           WalletAction,
                           WALLET_SERVICE_RATE,
                           WITHDRAW_RECORD_STATUS)
from horizon.serializers import (BaseSerializer,
                                 BaseModelSerializer,
                                 BaseListSerializer)
from horizon.main import make_random_string_char_and_number

import os
from decimal import Decimal


class WalletSerializer(BaseModelSerializer):
    def __init__(self, instance=None, data=None, **kwargs):
        if data:
            password = data.get('password')
            if password:
                password = make_password(password)
            request = kwargs.get('_request')
            user = getattr(request, 'user')
            _data = {'password': password,
                     'user_id': getattr(user, 'id')}
            super(WalletSerializer, self).__init__(data=_data, **kwargs)
        else:
            super(WalletSerializer, self).__init__(instance, **kwargs)

    class Meta:
        model = Wallet
        fields = '__all__'


class WalletResponseSerializer(BaseModelSerializer):
    class Meta:
        model = Wallet
        fields = ('user_id', 'balance', 'created', 'updated', 'extend')


class WalletDetailSerializer(BaseModelSerializer):
    def __init__(self, instance=None, data=None, **kwargs):
        if data:
            if '_request' in kwargs:
                request = kwargs['_request']
                data['user_id'] = request.user.id
            super(WalletDetailSerializer, self).__init__(data=data, **kwargs)
        else:
            super(WalletDetailSerializer, self).__init__(instance, **kwargs)

    class Meta:
        model = WalletTradeDetail
        fields = '__all__'


class WalletDetailListSerializer(BaseListSerializer):
    child = WalletDetailSerializer()


class WithdrawSerializer(BaseModelSerializer):
    def __init__(self, instance=None, data=None, **kwargs):
        if data:
            if 'request' in kwargs:
                request = kwargs.pop('request')
                data['user_id'] = request.user.id
                service_charge = '%.02f' % float(Decimal(WALLET_SERVICE_RATE) *
                                                 Decimal(data['amount_of_money']))
                payment_of_money = str(Decimal(data['amount_of_money']) -
                                       Decimal(service_charge))

                data['service_charge'] = service_charge
                data['payment_of_money'] = payment_of_money
            super(WithdrawSerializer, self).__init__(data=data, **kwargs)
        else:
            super(WithdrawSerializer, self).__init__(instance, **kwargs)

    class Meta:
        model = WithdrawRecord
        fields = '__all__'

    def save(self, request, amount_of_money, **kwargs):
        # 此处需要添加回滚操作
        # 冻结相应金额
        result = Wallet.update_blocked_money(request, amount_of_money)
        if isinstance(result, Exception):
            return result
        try:
            return super(WithdrawSerializer, self).save(**kwargs)
        except Exception as e:
            return e

    def update_status(self, request, instance, validated_data):
        """
        更新提现状态
        """
        if validated_data['status'] not in WITHDRAW_RECORD_STATUS.values():
            return ValueError('Status %d data is incorrect' % validated_data['status'])
        # 此处需要加上回滚操作
        try:
            instance = super(WithdrawSerializer, self).update(instance, validated_data)
        except Exception as e:
            return e
        wallet_instance = WalletAction().withdrawals(request, instance)
        if isinstance(wallet_instance, Exception):
            return wallet_instance
        return instance


class WithdrawRecordListSerializer(BaseListSerializer):
    child = WithdrawSerializer()


class BankCardSerializer(BaseModelSerializer):
    def __init__(self, instance=None, data=None, **kwargs):
        if data:
            super(BankCardSerializer, self).__init__(data=data, **kwargs)
        else:
            super(BankCardSerializer, self).__init__(instance, **kwargs)

    class Meta:
        model = BankCard
        fields = '__all__'

    def save(self, request, **kwargs):
        if not request.user.is_admin:
            return Exception('Permission denied.')
        try:
            return super(BankCardSerializer, self).save(**kwargs)
        except Exception as e:
            return e

    def delete(self, request, instance, **kwargs):
        if not request.user.is_admin:
            return Exception('Permission denied.')

        kwargs['status'] = 2
        kwargs['bank_card_number'] = '%s-%s' % (instance.bank_card_number,
                                                make_random_string_char_and_number(5))
        try:
            return super(BankCardSerializer, self).update(instance, kwargs)
        except Exception as e:
            return e


class BankCardListSerializer(BaseListSerializer):
    child = BankCardSerializer()

