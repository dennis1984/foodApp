# -*- coding:utf8 -*-
from __future__ import unicode_literals

from django.db import models
from django.utils.timezone import now
from dishes.models import Dishes, FoodCourt
from django.forms.models import model_to_dict
from decimal import Decimal

import json
import datetime


class Orders(models.Model):
    # orders_id = models.AutoField('订单ID', db_index=True)
    user_id = models.IntegerField('用户ID', db_index=True)
    # city = models.CharField('城市', max_length=200, default='')
    # meal_center = models.CharField('美食城', max_length=300, default='')
    food_court_name = models.CharField('美食城名字', max_length=200)
    city = models.CharField('所属城市', max_length=100, null=False)
    district = models.CharField('所属市区', max_length=100, null=False)
    mall = models.CharField('所属购物中心', max_length=200, default='')

    dishes_ids = models.TextField('订购列表', default='')
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
            return Dishes.objects.get(pk=pk)
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

        food_court_obj = FoodCourt.get_object(pk=request.user.food_court_id)
        if isinstance(food_court_obj, Exception):
            return food_court_obj

        orders_data = {'user_id': request.user.id,
                       # 'food_court_id': food_court_obj.id,
                       'food_court_name': food_court_obj.name,
                       'city': food_court_obj.city,
                       'district': food_court_obj.district,
                       'mall': food_court_obj.mall,
                       'dishes_ids': json.dumps(meal_ids, ensure_ascii=False, cls=DatetimeEncode),
                       'payable': total_payable,
                       }
        return orders_data

    @classmethod
    def get_object(cls, *args, **kwargs):
        try:
            return cls.objects.get(**kwargs)
        except Exception as e:
            return e

    @classmethod
    def get_object_by_orders_id(cls, orders_id):
        try:
            return cls.objects.get(pk=int(orders_id))
        except Exception as e:
            return e


class DatetimeEncode(json.JSONEncoder):
    def default(self, o):
        from django.db.models.fields.files import ImageFieldFile

        if isinstance(o, datetime.datetime):
            return str(o)
        elif isinstance(o, ImageFieldFile):
            return str(o)
        else:
            return json.JSONEncoder.default(self, o)

