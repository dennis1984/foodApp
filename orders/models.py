# -*- coding:utf8 -*-
from __future__ import unicode_literals

from django.db import models
from django.utils.timezone import now
from dishes.models import Dishes
from django.forms.models import model_to_dict
from decimal import Decimal

import json
import datetime


class Orders(models.Model):
    orders_id = models.CharField('订单ID', max_length=50, unique=True, db_index=True)
    user_id = models.IntegerField('用户ID', db_index=True)
    city = models.CharField('城市', max_length=200, default='')
    meal_center = models.CharField('美食城', max_length=300, default='')
    meal_ids = models.TextField('订购列表', default='')
    payable = models.CharField('订单总计', max_length=50, default='')
    payment_status = models.IntegerField('订单支付状态', default=0)    # 0:未支付 200:已支付 500:支付失败
    created = models.DateTimeField('创建时间', default=now)
    updated = models.DateTimeField('最后修改时间', auto_now=True)
    extend = models.TextField('扩展信息', default='', blank=True)

    class Meta:
        db_table = 'ys_orders'

    @classmethod
    def get_dishes_by_id(cls, pk):
        try:
            return Dishes.active_objects.get(pk=pk)
        except Dishes.DoesNotExist:
            raise Dishes.DoesNotExist

    @classmethod
    def make_orders_by_dishes_ids(cls, request, dishes_ids):
        meal_ids = []
        total_payable = '0'
        for item in dishes_ids:
            object_data = cls.get_dishes_by_id(item['dishes_id'])
            object_dict = model_to_dict(object_data)
            object_dict['count'] = item['count']
            meal_ids.append(object_dict)
            total_payable = str(Decimal(total_payable) + Decimal(object_data.price) * item['count'])

        orders_data = {'orders_id': '',
                       'user_id': request.user.id,
                       'city': '',
                       'meal_center': '',
                       'meal_ids': json.dumps(meal_ids, ensure_ascii=False, cls=DatetimeEncode),
                       'payable': total_payable,
                       }
        return orders_data


class DatetimeEncode(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime.datetime):
            return str(o)
        else:
            return json.JSONEncoder.default(self, o)

