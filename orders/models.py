# -*- coding:utf8 -*-
from __future__ import unicode_literals

from django.db import models
from django.utils.timezone import now
from dishes.models import Dishes, FoodCourt
from horizon.models import model_to_dict
from django.db import transaction
from decimal import Decimal

import json
import datetime


class Orders(models.Model):
    orders_id = models.CharField('订单ID', db_index=True, unique=True, max_length=30)
    user_id = models.IntegerField('用户ID', db_index=True)
    # city = models.CharField('城市', max_length=200, default='')
    # meal_center = models.CharField('美食城', max_length=300, default='')
    food_court_name = models.CharField('美食城名字', max_length=200)
    city = models.CharField('所属城市', max_length=100, null=False)
    district = models.CharField('所属市区', max_length=100, null=False)
    mall = models.CharField('所属购物中心', max_length=200, default='')

    dishes_ids = models.TextField('订购列表', default='')
    payable = models.CharField('订单总计', max_length=50, default='')
    payment_status = models.IntegerField('订单支付状态', default=0)    # 0:未支付 200:已支付 400: 已过期 500:支付失败

    # 支付方式：0:未指定支付方式 1：现金支付 2：微信支付 3：支付宝支付
    payment_mode = models.IntegerField('订单支付方式', default=0)
    created = models.DateTimeField('创建时间', default=now)
    updated = models.DateTimeField('最后修改时间', auto_now=True)
    extend = models.TextField('扩展信息', default='', blank=True)

    class Meta:
        db_table = 'ys_orders'

    def __unicode__(self):
        return self.orders_id

    @classmethod
    def get_dishes_by_id(cls, pk):
        try:
            return Dishes.objects.get(pk=pk)
        except Exception as e:
            return  e

    @classmethod
    def make_orders_by_dishes_ids(cls, request, dishes_ids):
        meal_ids = []
        total_payable = '0'
        for item in dishes_ids:
            object_data = cls.get_dishes_by_id(item['dishes_id'])
            if isinstance(object_data, Exception):
                return object_data

            object_dict = model_to_dict(object_data)
            object_dict['count'] = item['count']
            meal_ids.append(object_dict)
            total_payable = str(Decimal(total_payable) + Decimal(object_data.price) * item['count'])

        food_court_obj = FoodCourt.get_object(pk=request.user.food_court_id)
        if isinstance(food_court_obj, Exception):
            return food_court_obj

        orders_data = {'user_id': request.user.id,
                       'orders_id': OrdersIdGenerator.get_orders_id(),
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
            return cls.objects.get(orders_id=orders_id)
        except Exception as e:
            return e

    @classmethod
    def get_objects_list(cls, **kwargs):
        if 'user_id' not in kwargs:
            return Exception('user_id must be not null')

        _kwargs = {}
        if 'start_created' in kwargs:
            _kwargs['created__gte'] = kwargs['start_created']
        if 'end_created' in kwargs:
            _kwargs['created__lte'] = kwargs['end_created']
        if 'payment_status' in kwargs:
            _kwargs['payment_status'] = kwargs['payment_status']
        try:
            return cls.objects.filter(user_id=kwargs['user_id'], **_kwargs)
        except Exception as e:
            return e


def date_for_model():
    return now().date()


def ordersIdIntegerToString(orders_id):
    return "%06d" % orders_id


class OrdersIdGenerator(models.Model):
    date = models.DateField('日期', primary_key=True, default=date_for_model)
    orders_id = models.IntegerField('订单ID', default=1)
    created = models.DateTimeField('创建日期', default=now)
    updated = models.DateTimeField('最后更改日期', auto_now=True)

    class Meta:
        db_table = 'ys_orders_id_generator'

    def __unicode__(self):
        return str(self.date)

    @classmethod
    def get_orders_id(cls):
        date_day = date_for_model()
        orders_id = 0
        # 数据库加排它锁，保证订单号是唯一的
        with transaction.atomic():
            try:
                _instance = cls.objects.select_for_update().get(pk=date_day)
            except cls.DoesNotExist:
                cls().save()
                orders_id = 1
            else:
                orders_id = _instance.orders_id + 1
                _instance.orders_id = orders_id
                _instance.save()
        orders_id_string = ordersIdIntegerToString(orders_id)
        return '%s%s' % (date_day.strftime('%Y%m%d'), orders_id_string)


class DatetimeEncode(json.JSONEncoder):
    def default(self, o):
        from django.db.models.fields.files import ImageFieldFile

        if isinstance(o, datetime.datetime):
            return str(o)
        elif isinstance(o, ImageFieldFile):
            return str(o)
        else:
            return json.JSONEncoder.default(self, o)

