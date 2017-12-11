# -*- coding:utf8 -*-
from __future__ import unicode_literals
from rest_framework.request import Request
from django.http.request import HttpRequest

from django.db import models
from django.utils.timezone import now
from django.db import transaction
from decimal import Decimal

from orders.models import (Orders,
                           VerifyOrders,
                           ORDERS_ORDERS_TYPE)
from horizon.models import model_to_dict
from horizon.main import days_7_plus
from Consumer_App.cs_orders.models import SerialNumberGenerator
from users.models import BusinessUser
from horizon import main

import json
import datetime


WALLET_TRADE_DETAIL_TRADE_TYPE_DICT = {
    'recharge': 1,
    'income': 2,
    'withdraw': 3,
}
WALLET_ACTION_METHOD = ('recharge', 'income', 'withdraw')

WALLET_BLOCK_BALANCE = '0.00'
WALLET_SERVICE_RATE = '0.000'            # '0.006'
# 提现时钱包最小额度限制
WALLET_MIN_BALANCE = '300.00'

WITHDRAW_RECORD_STATUS = {
    'unpaid': 0,
    'finished': 200,
    'expired': 400,
    'failed': 500,
}
# 提现申请每周允许操作的时期
WITHDRAW_ACTION_ISO_WEEKDAY = (1, 2)    # 周一、周二


class WalletManager(models.Manager):
    def get(self, *args, **kwargs):
        kwargs['trade_status'] = 200
        return super(WalletManager, self).get(*args, **kwargs)

    def filter(self, *args, **kwargs):
        kwargs['trade_status'] = 200
        return super(WalletManager, self).filter(*args, **kwargs)


class Wallet(models.Model):
    """
    用户钱包
    """
    user_id = models.IntegerField('用户ID', db_index=True)
    balance = models.CharField('余额', max_length=16, default='0')
    blocked_money = models.CharField('冻结金额', max_length=16, default='0.00')
    password = models.CharField('支付密码', max_length=560, null=True)
    created = models.DateTimeField('创建时间', default=now)
    updated = models.DateTimeField('最后修改时间', auto_now=True)
    extend = models.TextField('扩展信息', default='', blank=True)

    class Meta:
        db_table = 'ys_wallet'

    def __unicode__(self):
        return str(self.user_id)

    @classmethod
    def has_enough_balance(cls, request, amount_of_money):
        wallet = cls.get_object(**{'user_id': request.user.id})
        if isinstance(wallet, Exception):
            return False
        try:
            return Decimal(wallet.balance) - \
                   Decimal(wallet.blocked_money) >= Decimal(amount_of_money)
        except:
            return False

    @classmethod
    def can_withdraw(cls, request):
        wallet = cls.get_object(**{'user_id': request.user.id})
        if isinstance(wallet, Exception):
            return False
        return Decimal(wallet.balance) - Decimal(wallet.blocked_money) \
               >= Decimal(WALLET_MIN_BALANCE)

    @classmethod
    def get_object(cls, **kwargs):
        try:
            return cls.objects.get(**kwargs)
        except Exception as e:
            return e

    @classmethod
    def create_wallet(cls, user_id):
        _ins = cls(**{'user_id': user_id})
        _ins.save()
        return _ins

    @classmethod
    def update_balance(cls, request, orders, method):
        verify_result = WalletActionBase().verify_action_params(
            orders=orders,
            request=request,
            method=method,
        )
        if verify_result is not True:
            return verify_result
        user_id = request.user.id
        amount_of_money = orders.payable
        _wallet = cls.get_object(**{'user_id': user_id})

        # 如果当前用户没有钱包，则创建钱包
        if isinstance(_wallet, Exception):
            _wallet = cls.create_wallet(user_id)
        try:
            total_fee = int(amount_of_money.split('.')[0])
        except Exception as e:
            return e
        if total_fee < 0:
            return ValueError('Amount of money Error')

        # 判断当前余额是否够用
        if method == WALLET_ACTION_METHOD[2]:
            if Decimal(_wallet.balance) < Decimal(amount_of_money):
                return ValueError('Balance is not enough')

        instance = None
        # 数据库加排它锁，保证更改信息是列队操作的，防止数据混乱
        with transaction.atomic():
            try:
                _instance = cls.objects.select_for_update().get(user_id=user_id)
            except cls.DoesNotExist:
                raise cls.DoesNotExist
            balance = _instance.balance
            # 提现
            if method == WALLET_ACTION_METHOD[2]:
                _instance.balance = str(Decimal(balance) - Decimal(amount_of_money))
            else:
                _instance.balance = str(Decimal(balance) + Decimal(amount_of_money))
            _instance.save()
            instance = _instance
        return instance

    @classmethod
    def update_blocked_money(cls, request, amount_of_money):
        if not cls.has_enough_balance(request, amount_of_money):
            return Exception('Your balance is not enough.')

        instance = None
        # 数据库加排它锁，保证更改信息是列队操作的，防止数据混乱
        with transaction.atomic():
            try:
                _instance = cls.objects.select_for_update().get(user_id=request.user.id)
            except cls.DoesNotExist:
                raise cls.DoesNotExist
            blocked_money = _instance.blocked_money
            _instance.blocked_money = str(Decimal(amount_of_money) + Decimal(blocked_money))
            _instance.save()
            instance = _instance
        return instance

    @classmethod
    def update_withdraw_balance(cls, user_id, amount_of_money):
        """
        提现
        """
        instance = None
        # 数据库加排它锁，保证更改信息是列队操作的，防止数据混乱
        with transaction.atomic():
            try:
                _instance = cls.objects.select_for_update().get(user_id=user_id)
            except cls.DoesNotExist:
                raise cls.DoesNotExist

            if Decimal(_instance.blocked_money) - Decimal(WALLET_BLOCK_BALANCE) < Decimal(amount_of_money) or \
                    Decimal(_instance.balance) - Decimal(WALLET_BLOCK_BALANCE) < Decimal(amount_of_money):
                return Exception('Your balance is not enough.')
            _instance.blocked_money = str(Decimal(_instance.blocked_money) - Decimal(amount_of_money))
            _instance.balance = str(Decimal(_instance.balance) - Decimal(amount_of_money))
            _instance.save()
            instance = _instance
        return instance


class WalletTradeDetail(models.Model):
    """
    交易明细
    """
    serial_number = models.CharField('流水号', unique=True, max_length=32)
    orders_id = models.CharField('订单ID', db_index=True, unique=True, max_length=32)
    user_id = models.IntegerField('用户ID', db_index=True)

    amount_of_money = models.CharField('金额', max_length=16)

    # 交易状态：0:未完成 200:已完成 500:交易失败
    trade_status = models.IntegerField('订单支付状态', default=200)
    # 交易类型 0: 未指定 1: 充值 2：订单收入 3: 提现
    trade_type = models.IntegerField('订单类型', default=0)

    created = models.DateTimeField('创建时间', default=now)
    extend = models.TextField('扩展信息', default='', blank=True)

    objects = WalletManager()

    class Meta:
        db_table = 'ys_wallet_trade_detail'
        ordering = ['-created']

    def __unicode__(self):
        return str(self.user_id)

    @classmethod
    def get_object(cls, **kwargs):
        try:
            return cls.objects.get(**kwargs)
        except Exception as e:
            return e

    @classmethod
    def filter_objects(cls, **kwargs):
        opts = cls._meta
        fields = []
        for f in opts.concrete_fields:
            fields.append(f.name)

        _kwargs = {}
        if 'start_created' in kwargs:
            _kwargs['created__gte'] = kwargs['start_created']
        if 'end_created' in kwargs:
            _kwargs['created__lte'] = main.make_time_delta_for_custom(kwargs['end_created'],
                                                                      hours=23,
                                                                      minutes=59,
                                                                      seconds=59)
        for key in kwargs:
            if key in fields:
                _kwargs[key] = kwargs[key]
        try:
            return cls.objects.filter(**_kwargs)
        except Exception as e:
            return e

    @classmethod
    def get_success_list(cls, **kwargs):
        kwargs['trade_status'] = 200
        return cls.filter_objects(**kwargs)


class WalletActionBase(object):
    """
    钱包相关功能
    """
    def get_wallet_trade_detail(self, orders_id):
        return WalletTradeDetail.get_object(**{'orders_id': orders_id})

    def verify_action_params(self, request, orders, method=None):
        if not isinstance(orders, (Orders, VerifyOrders)):
            return TypeError('Params orders must be Orders instance or '
                             'VerifyOrders instance.')

        wallet_detail = self.get_wallet_trade_detail(orders.orders_id)
        if not isinstance(wallet_detail, Exception):
            return TypeError('Cannot perform this action')
        if orders.user_id != request.user.id:
            return ValueError('The user ID and orders ID do not match')

        if method == WALLET_ACTION_METHOD[2]:  # 提现操作
            if not orders.is_success:
                return ValueError('Orders Data is Error')
            if not orders.is_recharge_orders:
                return ValueError('Orders Type is Error')
        else:    # 订单收入或充值（暂不支持）
            if not orders.is_success:
                return ValueError('Orders Data is Error')
            if not orders.is_consume_orders:
                return ValueError('Orders status is incorrect')

        if ('wallet_%s' % method) in ORDERS_ORDERS_TYPE:
            if orders.orders_type != ORDERS_ORDERS_TYPE['wallet_%s' % method]:
                return ValueError('Cannot perform this action')
        else:
            if orders.orders_type not in ORDERS_ORDERS_TYPE.values():
                return ValueError('Orders Type is incorrect')

        return True


class WalletAction(object):
    """
    钱包相关功能
    """
    def has_enough_balance(self, request, orders):
        if not isinstance(orders, (Orders, VerifyOrders)):
            return False
        return Wallet.has_enough_balance(request, orders.payable)

    def recharge(self, request, orders):
        """
        充值
        """

    def income(self, request, orders, gateway='auth'):
        """
        订单收入
        """
        if gateway == 'pay_callback':
            request = Request(HttpRequest)
            try:
                setattr(request.user, 'id', orders.user_id)
            except Exception as e:
                return e
        # 订单收入
        result = Wallet.update_balance(request=request,
                                       orders=orders,
                                       method=WALLET_ACTION_METHOD[1])
        # 生成交易记录
        _trade = WalletTradeAction().create(request, orders)
        if isinstance(_trade, Exception):
            return _trade
        return result

    def withdrawals(self, request, withdraw_record):
        """
        提现
        """
        if not request.user.is_admin:
            return Exception('Permission denied.')
        if not isinstance(withdraw_record, WithdrawRecord):
            return TypeError('Params [withdraw_record] data type error.')
        if withdraw_record.status != WITHDRAW_RECORD_STATUS['finished']:
            return TypeError('Cannot perform this action.')

        # 提现
        instance = Wallet.update_withdraw_balance(withdraw_record.user_id,
                                                  withdraw_record.amount_of_money)
        if isinstance(instance, Exception):
            return instance
        # 生成交易记录
        _trade = WalletTradeAction().create(request, withdraw_record, method='withdraw')
        if isinstance(_trade, Exception):
            return _trade
        return instance


class WalletTradeAction(object):
    """
    钱包明细相关功能
    """
    def create(self, request, orders, method='income'):
        """
        创建交易明细（包含：充值（暂不支持）、订单收入和提现的交易明细）
        """
        serial_number = SerialNumberGenerator.get_serial_number()
        if method == 'income':
            if not isinstance(orders, (Orders, VerifyOrders)):
                return TypeError('Orders data error')
            if orders.orders_type not in ORDERS_ORDERS_TYPE.values():
                return ValueError('Orders data error')
            if not orders.is_success:
                return ValueError('Orders data error')

            # 交易类型：订单收入
            trade_type = WALLET_TRADE_DETAIL_TRADE_TYPE_DICT['income']

            kwargs = {'orders_id': orders.orders_id,
                      'user_id': request.user.id,
                      'trade_type': trade_type,
                      'amount_of_money': orders.payable}
        else:
            kwargs = {'trade_type': WALLET_TRADE_DETAIL_TRADE_TYPE_DICT['withdraw'],   # 交易类型：提现
                      'orders_id': 'TX-%s-%s' % (orders.user_id,
                                                 datetime.datetime.strftime(orders.created, '%Y%m%d%H%M%S')),
                      'user_id': orders.user_id,
                      'amount_of_money': orders.amount_of_money,
                      }

        kwargs['serial_number'] = serial_number
        wallet_detail = WalletTradeDetail(**kwargs)
        try:
            wallet_detail.save()
        except Exception as e:
            return e
        return wallet_detail


class WithdrawRecord(models.Model):
    """
    提现记录
    """
    user_id = models.IntegerField('用户ID', db_index=True)

    amount_of_money = models.CharField('申请提现金额', max_length=16)
    service_charge = models.CharField('手续费', max_length=16)
    payment_of_money = models.CharField('实际提现金额', max_length=16)
    account_id = models.IntegerField('提现到账账户')

    # 提现状态：0:审核中 200:已完成 400:提现申请已过期 500:审核不通过
    status = models.IntegerField('提现状态', default=0)

    expires = models.DateTimeField('申请提现过期时间', default=days_7_plus)
    created = models.DateTimeField('创建时间', default=now)
    updated = models.DateTimeField('更新实际', auto_now=True)
    extend = models.TextField('扩展信息', default='', blank=True)

    class Meta:
        db_table = 'ys_wallet_withdraw_record'
        ordering = ['-created']

    def __unicode__(self):
        return str(self.user_id)

    @classmethod
    def get_object(cls, **kwargs):
        try:
            return cls.objects.get(**kwargs)
        except Exception as e:
            return e

    @classmethod
    def get_unpaid_object(cls, **kwargs):
        kwargs['status'] = WITHDRAW_RECORD_STATUS['unpaid']
        return cls.get_object(**kwargs)

    @classmethod
    def filter_objects(cls, **kwargs):
        try:
            return cls.objects.filter(**kwargs)
        except Exception as e:
            return e


class BankCardManager(models.Manager):
    def get(self, *args, **kwargs):
        kwargs['status'] = 1
        return super(BankCardManager, self).get(*args, **kwargs)

    def filter(self, *args, **kwargs):
        kwargs['status'] = 1
        return super(BankCardManager, self).filter(*args, **kwargs)


class BankCard(models.Model):
    """
    银行卡信息
    """
    user_id = models.IntegerField('用户ID', db_index=True)

    bank_card_number = models.CharField('银行卡', max_length=30)
    bank_name = models.CharField('银行名称', max_length=50)
    account_name = models.CharField('开户名', max_length=20)

    # 银行卡绑定状态 1：已绑定，2：已解除
    status = models.IntegerField('绑定状态', default=1)
    created = models.DateTimeField('创建时间', default=now)
    updated = models.DateTimeField('更新实际', auto_now=True)

    objects = BankCardManager()

    class Meta:
        db_table = 'ys_wallet_bank_card'
        ordering = ['-created']
        unique_together = ('bank_card_number', 'status')

    def __unicode__(self):
        return str(self.user_id)

    @classmethod
    def get_object(cls, **kwargs):
        try:
            return cls.objects.get(**kwargs)
        except Exception as e:
            return e

    @classmethod
    def does_exist_by_pk(cls, pk):
        ins = cls.get_object(pk=pk)
        if isinstance(ins, Exception):
            return False
        return True

    @classmethod
    def filter_objects(cls, **kwargs):
        try:
            return cls.objects.filter(**kwargs)
        except Exception as e:
            return e

    @classmethod
    def filter_perfect_details(cls, request, **kwargs):
        instances = cls.filter_objects(**kwargs)
        if isinstance(instances, Exception):
            return instances

        users_dict = {}
        details = []
        for ins in instances:
            if not request.user.is_admin:
                ins.bank_card_number = ins.security_card_number

            detail = model_to_dict(ins)
            user = users_dict.get(ins.user_id)
            if not user:
                user = BusinessUser.get_object(pk=ins.user_id)
                users_dict[ins.user_id] = user
            detail['chinese_people_id'] = user.chinese_people_id
            details.append(detail)
        return details

    @property
    def security_card_number(self):
        card_num_list = self.bank_card_number.split()
        card_num_list[-2] = '*' * 4
        return ' '.join(card_num_list)
