# -*- coding:utf8 -*-
from __future__ import unicode_literals

from django.db import models
from django.utils.timezone import now
from dishes.models import Dishes, FoodCourt
from users.models import BusinessUser
from horizon.models import model_to_dict
from django.db import transaction
from decimal import Decimal

import json
import datetime


class Orders(models.Model):
    orders_id = models.CharField('订单ID', db_index=True, unique=True, max_length=30)
    user_id = models.IntegerField('用户ID', db_index=True)
    food_court_name = models.CharField('美食城名字', max_length=200)
    city = models.CharField('所属城市', max_length=100, null=False)
    district = models.CharField('所属市区', max_length=100, null=False)
    mall = models.CharField('所属购物中心', max_length=200, default='')

    dishes_ids = models.TextField('订购列表', default='')
    payable = models.CharField('订单总计', max_length=50, default='')

    # 0:未支付 200:已支付 400: 已过期 500:支付失败
    payment_status = models.IntegerField('订单支付状态', default=0)
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
    def get_objects_list(cls, request, **kwargs):
        opts = cls._meta
        fields = []
        for f in opts.concrete_fields:
            fields.append(f.name)

        _kwargs = {}
        if request.user.is_admin:
            if 'user_id' in kwargs:
                _kwargs['user_id'] = kwargs['user_id']
        else:
            _kwargs['user_id'] = request.user.id
        for key in kwargs:
            if key not in fields:
                continue
            if 'start_created' in kwargs:
                _kwargs['created__gte'] = kwargs['start_created']
            elif 'end_created' in kwargs:
                _kwargs['created__lte'] = kwargs['end_created']
            else:
                _kwargs[key] = kwargs[key]

        try:
            return cls.objects.filter(**_kwargs)
        except Exception as e:
            return e


def get_sale_list(request, **kwargs):
    if request.user.is_admin and 'user_id' not in kwargs:
        return get_sale_list_by_admin(request, **kwargs)
    else:
        return get_sale_list_by_user(request, **kwargs)


def get_sale_list_by_user(request, **kwargs):
    """
    销售统计（普通用户）
    """
    # 支付状态为：已支付
    kwargs['payment_status'] = 200
    # 如果参数没有选择时间范围，默认选取当前时间至向前30天的数据
    if not ('start_created' in kwargs or 'end_created' in kwargs):
        kwargs['start_created'] = now().date() - datetime.timedelta(days=30)
        kwargs['end_created'] = now().date()
    orders_list = Orders.get_objects_list(request, **kwargs)
    if isinstance(orders_list, Exception):
        return orders_list

    sale_dict = {}
    for item in orders_list:
        datetime_day = item.created.date()
        sale_detail = sale_dict.get(datetime_day, {'total_count': 0, 'total_payable': '0'})
        sale_detail['total_count'] += 1
        sale_detail['total_payable'] = Decimal(sale_detail['total_payable']) + Decimal(item.payable)
        sale_dict[datetime_day] = sale_detail
    results = []
    for key, value in sale_dict.items():
        sale_detail = value
        sale_detail['date'] = str(key)
        sale_detail['total_payable'] = str(sale_detail['total_payable'])
        results.append(sale_detail)
    results.sort(key=lambda x: x['date'], reverse=True)
    return results


def get_sale_list_by_admin(request, **kwargs):
    """
    销售统计（管理员）
    """
    # 支付状态为：已支付
    kwargs['payment_status'] = 200
    # 如果参数没有选择时间范围，默认选取当前时间至向前30天的数据
    if not ('start_created' in kwargs or 'end_created' in kwargs):
        kwargs['start_created'] = now().date() - datetime.timedelta(days=30)
        kwargs['end_created'] = now().date()
    orders_list = Orders.get_objects_list(request, **kwargs)
    if isinstance(orders_list, Exception):
        return orders_list

    users_list = BusinessUser.objects.all()
    users_dict = {item.id: item for item in users_list}

    sale_dict = {}
    for item in orders_list:
        user_obj = users_dict.get(item.user_id)
        business_name = getattr(user_obj, 'business_name', 'none')
        sale_detail = sale_dict.get(business_name, {'total_count': 0,
                                                    'total_payable': '0',
                                                    'user_id': item.user_id,
                                                    'start_created': now().date(),
                                                    })
        if item.created.date() < sale_detail['start_created']:
            sale_detail['start_created'] = item.created.date()
        sale_detail['total_count'] += 1
        sale_detail['total_payable'] = Decimal(sale_detail['total_payable']) + Decimal(item.payable)
        sale_dict[business_name] = sale_detail
    results = []
    for key, value in sale_dict.items():
        sale_detail = value
        sale_detail['date'] = '%s--%s' % (kwargs.get('start_created', sale_detail['start_created']),
                                          kwargs.get('end_created', now().date()))
        sale_detail['business_name'] = key
        sale_detail['total_payable'] = str(sale_detail['total_payable'])
        results.append(sale_detail)
    results.sort(key=lambda x: x['business_name'], reverse=True)
    return results


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

