# -*- coding:utf8 -*-
from __future__ import unicode_literals
from django.db import models, transaction
from django.utils.timezone import now
from orders.models import ORDERS_ORDERS_TYPE, ORDERS_PAYMENT_STATUS

from horizon import main
from horizon.main import minutes_15_plus


class ConsumeOrders(models.Model):
    """
    消费订单（子订单）
    """
    orders_id = models.CharField('订单ID', db_index=True, unique=True, max_length=32)
    user_id = models.IntegerField('用户ID', db_index=True)

    business_name = models.CharField('商户名字', max_length=200)
    business_id = models.IntegerField('商户ID')
    food_court_id = models.IntegerField('美食城ID')
    food_court_name = models.CharField('美食城名字', max_length=200)

    dishes_ids = models.TextField('订购列表', default='')

    total_amount = models.CharField('订单总计', max_length=16)
    member_discount = models.CharField('会员优惠', max_length=16, default='0')
    other_discount = models.CharField('其他优惠', max_length=16, default='0')
    payable = models.CharField('应付金额', max_length=16)

    # 0:未支付 200:已支付 201:待消费 206:已完成 400: 已过期 500:支付失败
    payment_status = models.IntegerField('订单支付状态', default=201)
    # 支付方式：0:未指定支付方式 1：钱包支付 2：微信支付 3：支付宝支付
    payment_mode = models.IntegerField('订单支付方式', default=0)
    # 订单类型 0: 未指定 101: 在线订单 102：堂食订单 103：外卖订单
    #         201: 钱包充值订单  (预留：202：钱包消费订单 203: 钱包提现)
    orders_type = models.IntegerField('订单类型', default=ORDERS_ORDERS_TYPE['online'])
    # 所属主订单
    master_orders_id = models.CharField('所属主订单订单ID', max_length=32)
    # 是否点评过  0: 未点评过  1： 已经完成点评
    is_commented = models.IntegerField('是否点评过', default=0)

    created = models.DateTimeField('创建时间', default=now)
    updated = models.DateTimeField('最后修改时间', auto_now=True)
    expires = models.DateTimeField('订单过期时间', default=minutes_15_plus)
    extend = models.TextField('扩展信息', default='', blank=True)

    # objects = OrdersManager()

    class Meta:
        db_table = 'ys_consume_orders'
        app_label = 'Consumer_App.cs_orders.models.ConsumeOrders'
        ordering = ['-orders_id']

    def __unicode__(self):
        return self.orders_id

    @classmethod
    def get_object(cls, **kwargs):
        try:
            return cls.objects.get(**kwargs)
        except Exception as e:
            return e


class ConsumeOrdersAction(object):
    """
    子订单更新
    """
    def get_orders_instance(self, orders_id):
        return ConsumeOrders.get_object(**{'orders_id': orders_id})

    def update_payment_status_to_finished(self, orders_id):
        """
        更新核销订单的支付状态为结束
        return: orders instance: 成功
                Exception：失败
        """
        orders = self.get_orders_instance(orders_id)
        if isinstance(orders, Exception):
            return orders
        if orders.payment_status != ORDERS_PAYMENT_STATUS['consuming']:
            return ValueError('The orders payment status is incorrect.')

        orders.payment_status = ORDERS_PAYMENT_STATUS['finished']
        try:
            orders.save()
        except Exception as e:
            return e
        return orders


class ConfirmConsumeManager(models.Manager):
    def get(self, *args, **kwargs):
        kwargs['expires__gt'] = now()
        return super(ConfirmConsumeManager, self).get(*args, **kwargs)

    def filter(self, *args, **kwargs):
        kwargs['expires__gt'] = now()
        return super(ConfirmConsumeManager, self).filter(*args, **kwargs)


class ConfirmConsume(models.Model):
    user_id = models.IntegerField('用户ID')
    random_string = models.CharField('随机字符串', db_index=True, max_length=64)
    expires = models.DateTimeField('过期时间', default=main.minutes_5_plus)
    created = models.DateTimeField('创建日期', default=now)

    objects = ConfirmConsumeManager()

    class Meta:
        db_table = 'ys_confirm_consume_qrcode'
        app_label = 'Consumer_App.cs_orders.models.ConfirmConsume'

    def __unicode__(self):
        return str(self.user_id)

    @classmethod
    def get_object(cls, **kwargs):
        try:
            return cls.objects.get(**kwargs)
        except Exception as e:
            return e


def date_for_model():
    return now().date()


class SerialNumberGenerator(models.Model):
    date = models.DateField('日期', primary_key=True, default=date_for_model)
    serial_number = models.IntegerField('流水号', default=1)
    created = models.DateTimeField('创建日期', default=now)
    updated = models.DateTimeField('最后更改日期', auto_now=True)

    class Meta:
        db_table = 'ys_serial_number_generator'

    def __unicode__(self):
        return str(self.date)

    @classmethod
    def int_to_string(cls, serial_no):
        return "%06d" % serial_no

    @classmethod
    def get_serial_number(cls):
        date_day = date_for_model()
        # 数据库加排它锁，保证交易流水号是唯一的
        with transaction.atomic():
            try:
                _instance = cls.objects.select_for_update().get(pk=date_day)
            except cls.DoesNotExist:
                cls().save()
                serial_no = 1
            else:
                serial_no = _instance.serial_number + 1
                _instance.serial_number = serial_no
                _instance.save()
        serial_no_str = cls.int_to_string(serial_no)
        return 'LS%s%s' % (date_day.strftime('%Y%m%d'), serial_no_str)
