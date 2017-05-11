# -*- coding:utf8 -*-

from __future__ import unicode_literals

from django.db import models
from django.utils.timezone import now


class Orders(models.Model):
    order_id = models.CharField('订单ID', max_length=50, unique=True, null=False)
    user_id = models.IntegerField('用户ID', db_index=True, null=False)
    city = models.CharField('城市', max_length=200, default='')
    meal_center = models.CharField('美食城', max_length=300, default='')
    meal_ids = models.TextField('订购列表', default='')
    payable = models.CharField('订单总计', max_length=50, default='')
    payment_status = models.IntegerField('订单支付状态', default=0)
    created = models.DateTimeField('创建时间', default=now)
    updated = models.DateTimeField('最后修改时间', auto_now=True)
    extend = models.TextField('扩展信息', default='')

    class Meta:
        db_table = 'ys_orders'


