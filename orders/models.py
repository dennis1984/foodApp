# -*- coding:utf8 -*-
from __future__ import unicode_literals

from django.db import models
from django.utils.timezone import now
from dishes.models import Dishes, FoodCourt
from users.models import BusinessUser
from horizon.models import model_to_dict, get_perfect_filter_params
from horizon.main import minutes_15_plus
from django.db import transaction
from decimal import Decimal

from Consumer_App.cs_users.models import ConsumerUser

import copy
import json
import datetime

ORDERS_PAYMENT_STATUS = {
    'unpaid': 0,
    'paid': 200,
    'consuming': 201,
    'finished': 206,
    'expired': 400,
    'failed': 500,
}

ORDERS_PAYMENT_MODE = {
    'unknown': 0,
    'cash': 1,
    'wxpay': 2,
    'alipay': 3,
}

ORDERS_ORDERS_TYPE = {
    'unknown': 0,
    'online': 101,
    'business': 102,
    'take_out': 103,
    'wallet_withdraw': 203,
}


class OrdersManager(models.Manager):
    def get(self, *args, **kwargs):
        object_data = super(OrdersManager, self).get(*args, **kwargs)
        if now() >= object_data.expires and object_data.payment_status == 0:
            object_data.payment_status = 400
        return object_data

    def filter(self, *args, **kwargs):
        object_data = super(OrdersManager, self).filter(*args, **kwargs)
        for item in object_data:
            if now() >= item.expires and item.payment_status == 0:
                item.payment_status = 400
        return object_data


class Orders(models.Model):
    orders_id = models.CharField('订单ID', db_index=True, unique=True, max_length=30)
    user_id = models.IntegerField('用户ID', db_index=True)
    food_court_id = models.IntegerField('美食城ID')
    food_court_name = models.CharField('美食城名字', max_length=200)
    business_name = models.CharField('商户名字', max_length=100)

    dishes_ids = models.TextField('订购列表', default='')
    # 订购列表详情
    # [
    #  {'id': 1, ...},   # 菜品详情
    #  {'id': 2, ...}, ...
    # ]
    #
    total_amount = models.CharField('订单总计', max_length=16, default='0')
    member_discount = models.CharField('会员优惠', max_length=16, default='0')
    online_discount = models.CharField('在线下单优惠', max_length=16, default='0')
    other_discount = models.CharField('其他优惠', max_length=16, default='0')
    payable = models.CharField('订单总计', max_length=16, default='0')

    # 0:未支付 200:已支付 400: 已过期 500:支付失败
    payment_status = models.IntegerField('订单支付状态', default=0)
    # 支付方式：0:未指定支付方式 1：现金支付 2：微信支付 3：支付宝支付
    payment_mode = models.IntegerField('订单支付方式', default=0)
    # 订单类型 0: 未指定 101: 在线订单 102：堂食订单 103：外卖订单
    orders_type = models.IntegerField('订单类型', default=102)

    created = models.DateTimeField('创建时间', default=now)
    updated = models.DateTimeField('最后修改时间', auto_now=True)
    expires = models.DateTimeField('订单过期时间', default=minutes_15_plus)
    extend = models.TextField('扩展信息', default='', blank=True)

    objects = OrdersManager()

    class Meta:
        db_table = 'ys_orders'
        ordering = ['-orders_id']

    def __unicode__(self):
        return self.orders_id

    @property
    def is_expired(self):
        if now() >= self.expires:
            return True
        return False

    @property
    def is_success(self):
        """
        订单是否完成
        :return:
        """
        if self.payment_status == ORDERS_PAYMENT_STATUS['paid']:
            return True
        return False

    @property
    def is_consume_orders(self):
        """
        消费订单
        """
        if self.orders_type not in (ORDERS_ORDERS_TYPE['wallet_withdraw'],
                                    ORDERS_ORDERS_TYPE['unknown']):
            return True
        return False

    @classmethod
    def get_dishes_by_id(cls, pk):
        try:
            return Dishes.objects.get(pk=pk)
        except Exception as e:
            return  e

    @classmethod
    def make_orders_by_dishes_ids(cls, request, dishes_ids):
        meal_ids = []
        total_amount = '0'
        member_discount = '0'
        other_discount = '0'
        for item in dishes_ids:
            object_data = cls.get_dishes_by_id(item['dishes_id'])
            if isinstance(object_data, Exception):
                return object_data

            object_dict = model_to_dict(object_data)
            object_dict['count'] = item['count']
            meal_ids.append(object_dict)
            total_amount = str(Decimal(total_amount) +
                               Decimal(object_data.price) * item['count'])

        food_court_obj = FoodCourt.get_object(pk=request.user.food_court_id)
        if isinstance(food_court_obj, Exception):
            return food_court_obj

        orders_data = {'user_id': request.user.id,
                       'orders_id': OrdersIdGenerator.get_orders_id(),
                       'food_court_id': request.user.food_court_id,
                       'food_court_name': food_court_obj.name,
                       'business_name': request.user.business_name,
                       'dishes_ids': json.dumps(meal_ids, ensure_ascii=False,
                                                cls=DatetimeEncode),
                       'total_amount': total_amount,
                       'member_discount': member_discount,
                       'other_discount': other_discount,
                       'payable': str(Decimal(total_amount) -
                                      Decimal(member_discount) -
                                      Decimal(other_discount))
                       }
        return orders_data

    @property
    def dishes_ids_json_detail(self):
        import json
        results = self.dishes_ids_detail
        return json.dumps(results)

    @property
    def dishes_ids_detail(self):
        results = []
        instance_list = json.loads(self.dishes_ids)
        for _instance in instance_list:
            _ins_dict = {'count': _instance['count'],
                         'id': _instance['id'],
                         'is_recommend': _instance['is_recommend'],
                         'price': _instance['price'],
                         'size': _instance['size'],
                         'title': _instance['title'],
                         'user_id': _instance['user_id']}
            results.append(_ins_dict)
        return results

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
        if 'start_created' in kwargs:
            _kwargs['created__gte'] = kwargs['start_created']
        if 'end_created' in kwargs:
            _kwargs['created__lte'] = kwargs['end_created']
        if 'expires__gt' in kwargs:
            _kwargs['expires__gt'] = kwargs['expires__gt']
        for key in kwargs:
            if key in fields:
                _kwargs[key] = kwargs[key]

        try:
            return cls.objects.filter(**_kwargs)
        except Exception as e:
            return e

    @classmethod
    def filter_paying_orders_list(cls, request, **kwargs):
        """
        获取待支付订单
        """
        kwargs['payment_status'] = ORDERS_PAYMENT_STATUS['unpaid']
        kwargs['expires__gt'] = now()
        orders_list = cls.get_objects_list(request, **kwargs)
        return cls.make_instances_to_dict(orders_list)

    @classmethod
    def filter_finished_orders_list(cls, request, **kwargs):
        """
        获取已支付完成订单
        """
        kwargs['payment_status'] = ORDERS_PAYMENT_STATUS['paid']
        orders_list = cls.get_objects_list(request, **kwargs)
        return cls.make_instances_to_dict(orders_list)

    @classmethod
    def make_instances_to_dict(cls, orders_list):
        if isinstance(orders_list, cls):
            orders_list = [orders_list]
        detail_list = []
        for orders in orders_list:
            item_dict = model_to_dict(orders)
            item_dict['dishes_ids'] = json.loads(item_dict['dishes_ids'])
            item_dict['is_master'] = True
            item_dict['consumer_id'] = None
            detail_list.append(item_dict)
        return detail_list

    @classmethod
    def update_payment_status_by_pay_callback(cls, orders_id, validated_data):
        if not isinstance(validated_data, dict):
            raise ValueError('Parameter error')

        payment_status = validated_data.get('payment_status')
        payment_mode = validated_data.get('payment_mode')
        if payment_status not in (200, 400, 500):
            raise ValueError('Payment status must in range [200, 400, 500]')
        if payment_mode not in [2, 3]:    # 微信支付和支付宝支付
            raise ValueError('Payment mode must in range [2, 3]')
        instance = None
        # 数据库加排它锁，保证更改信息是列队操作的，防止数据混乱
        with transaction.atomic():
            try:
                _instance = cls.objects.select_for_update().get(orders_id=orders_id)
            except cls.DoesNotExist:
                raise cls.DoesNotExist
            if _instance.payment_status != 0:
                raise Exception('Cannot perform this action')
            _instance.payment_status = payment_status
            _instance.payment_mode = payment_mode
            _instance.save()
            instance = _instance
        return instance


class VerifyOrders(models.Model):
    """
    核销订单
    """
    orders_id = models.CharField('订单ID', db_index=True, unique=True, max_length=32)
    user_id = models.IntegerField('用户ID', db_index=True)

    business_name = models.CharField('商户名字', max_length=200)
    food_court_id = models.IntegerField('美食城ID')
    food_court_name = models.CharField('美食城名字', max_length=200)
    consumer_id = models.IntegerField('消费者ID')

    dishes_ids = models.TextField('订购列表', default='')

    total_amount = models.CharField('订单总计', max_length=16)
    member_discount = models.CharField('会员优惠', max_length=16, default='0')
    online_discount = models.CharField('在线下单优惠', max_length=16, default='0')
    other_discount = models.CharField('其他优惠', max_length=16, default='0')
    payable = models.CharField('应付金额', max_length=16)

    # 0:未支付 200:已支付 201:待消费 206:已完成 400: 已过期 500:支付失败
    payment_status = models.IntegerField('订单支付状态', default=201)
    # 支付方式：0:未指定支付方式 1：钱包支付 2：微信支付 3：支付宝支付
    payment_mode = models.IntegerField('订单支付方式', default=0)
    # 订单类型 0: 未指定 101: 在线订单 102：堂食订单 103：外卖订单
    orders_type = models.IntegerField('订单类型', default=101)

    created = models.DateTimeField('创建时间', default=now)
    updated = models.DateTimeField('最后修改时间', auto_now=True)
    expires = models.DateTimeField('订单过期时间', default=minutes_15_plus)
    extend = models.TextField('扩展信息', default='', blank=True)

    # objects = OrdersManager()

    class Meta:
        db_table = 'ys_verify_orders'
        ordering = ['-orders_id']

    def __unicode__(self):
        return self.orders_id

    @property
    def is_expired(self):
        if now() >= self.expires:
            return True
        return False

    @property
    def is_success(self):
        """
        订单是否完成
        :return:
        """
        if self.payment_status == ORDERS_PAYMENT_STATUS['finished']:
            return True
        return False

    @property
    def is_consume_orders(self):
        """
        消费订单
        """
        if self.orders_type not in (ORDERS_ORDERS_TYPE['wallet_withdraw'],
                                    ORDERS_ORDERS_TYPE['unknown']):
            return True
        return False

    @classmethod
    def get_object(cls, **kwargs):
        try:
            return cls.objects.get(**kwargs)
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
        if 'start_created' in kwargs:
            _kwargs['created__gte'] = kwargs['start_created']
        if 'end_created' in kwargs:
            _kwargs['created__lte'] = kwargs['end_created']
        for key in kwargs:
            if key in fields:
                _kwargs[key] = kwargs[key]

        try:
            return cls.objects.filter(**_kwargs)
        except Exception as e:
            return e

    @classmethod
    def filter_consuming_orders_list(cls, request, is_detail=True, **kwargs):
        """
        获取待消费订单
        """
        kwargs['payment_status'] = ORDERS_PAYMENT_STATUS['consuming']
        orders_list = cls.get_objects_list(request, **kwargs)
        if is_detail:
            return cls.make_instances_to_dict(orders_list)
        else:
            return list(orders_list)

    @classmethod
    def filter_finished_orders_list(cls, request, is_detail=True, **kwargs):
        """
        获取已完成订单
        """
        kwargs['payment_status'] = ORDERS_PAYMENT_STATUS['finished']
        orders_list = cls.get_objects_list(request, **kwargs)
        if is_detail:
            return cls.make_instances_to_dict(orders_list)
        else:
            return list(orders_list)

    @classmethod
    def make_instances_to_dict(cls, orders_list):
        if isinstance(orders_list, cls):
            orders_list = list(orders_list)
        detail_list = []
        for orders in orders_list:
            item_dict = model_to_dict(orders)
            item_dict['dishes_ids'] = json.loads(item_dict['dishes_ids'])
            item_dict['is_master'] = False
            detail_list.append(item_dict)
        return detail_list


class SaleListAction(object):
    """
    销售统计
    """
    @classmethod
    def get_sale_list(cls, request, **kwargs):
        if request.user.is_admin and 'user_id' not in kwargs:
            return cls.get_sale_list_by_admin(request, **kwargs)
        else:
            return cls.get_orders_sale_list(request, **kwargs)

    @classmethod
    def get_finished_orders_list(cls, request, **kwargs):
        """
        获取支付完成和核销完成的订单列表
        """
        # 支付订单支付状态为：已支付
        kwargs['payment_status'] = ORDERS_PAYMENT_STATUS['paid']
        # 和小订单支付状态为：已完成
        v_kwargs = copy.deepcopy(kwargs)
        v_kwargs['payment_status'] = ORDERS_PAYMENT_STATUS['finished']
        # 如果参数没有选择时间范围，默认选取当前时间至向前30天的数据
        if not ('start_created' in kwargs or 'end_created' in kwargs):
            kwargs['start_created'] = now().date() - datetime.timedelta(days=30)
            kwargs['end_created'] = now().date()
        orders_list = Orders.get_objects_list(request, **kwargs)
        verify_orders_list = VerifyOrders.get_objects_list(request, **v_kwargs)
        return orders_list, verify_orders_list


    @classmethod
    def get_orders_sale_list(cls, request, **kwargs):
        """
        订单销售统计（普通用户）
        """
        orders_list, verify_orders_list = cls.get_finished_orders_list(request, **kwargs)
        if isinstance(orders_list, Exception):
            return orders_list
        if isinstance(verify_orders_list, Exception):
            return verify_orders_list

        init_dict = {'total_count': 0,
                     'total_payable': '0',
                     'cash': {'count': 0, 'payable': '0'},
                     'wxpay': {'count': 0, 'payable': '0'},
                     'alipay': {'count': 0, 'payable': '0'},
                     'yspay': {'count': 0, 'payable': '0'},
                     }
        sale_dict = {}
        for item in orders_list:
            datetime_day = item.created.date()
            sale_detail = sale_dict.get(datetime_day, copy.deepcopy(init_dict))
            sale_detail['total_count'] += 1
            sale_detail['total_payable'] = str(Decimal(sale_detail['total_payable']) +
                                               Decimal(item.payable))
            if item.payment_mode == ORDERS_PAYMENT_MODE['cash']:
                sale_detail['cash']['count'] += 1
                sale_detail['cash']['payable'] = str(Decimal(sale_detail['cash']['payable']) +
                                                     Decimal(item.payable))
            elif item.payment_mode == ORDERS_PAYMENT_MODE['wxpay']:
                sale_detail['wxpay']['count'] += 1
                sale_detail['wxpay']['payable'] = str(Decimal(sale_detail['wxpay']['payable']) +
                                                      Decimal(item.payable))
            elif item.payment_mode == ORDERS_PAYMENT_MODE['alipay']:
                sale_detail['alipay']['count'] += 1
                sale_detail['alipay']['payable'] = str(Decimal(sale_detail['alipay']['payable']) +
                                                       Decimal(item.payable))
            else:
                pass
            sale_dict[datetime_day] = sale_detail

        for item in verify_orders_list:
            datetime_day = item.created.date()
            sale_detail = sale_dict.get(datetime_day, copy.deepcopy(init_dict))
            sale_detail['total_count'] += 1
            sale_detail['total_payable'] = str(Decimal(sale_detail['total_payable']) +
                                               Decimal(item.payable))
            sale_detail['yspay']['count'] += 1
            sale_detail['yspay']['payable'] = str(Decimal(sale_detail['yspay']['payable']) +
                                                  Decimal(item.payable))
            sale_dict[datetime_day] = sale_detail

        results = []
        for key, value in sale_dict.items():
            sale_detail = value
            sale_detail['date'] = str(key)
            results.append(sale_detail)
        results.sort(key=lambda x: x['date'], reverse=True)
        return results

    @classmethod
    def get_dishes_sale_list(cls, request, **kwargs):
        """
        菜品销量统计
        """
        orders_list, verify_orders_list = cls.get_finished_orders_list(request, **kwargs)
        if isinstance(orders_list, Exception):
            return orders_list
        if isinstance(verify_orders_list, Exception):
            return verify_orders_list

        dishes_dict = {}
        for item in list(orders_list) + list(verify_orders_list):
            datetime_day = item.created.date()
            sale_detail = dishes_dict.get(datetime_day, {})
            for dishes_item in json.loads(item.dishes_ids):
                dishes_id = dishes_item['id']
                sale_tmp = {'dishes_id': dishes_id,
                            'title': dishes_item['title'],
                            'size': dishes_item['size'],
                            'size_detail': dishes_item.get('size_detail'),
                            'count': dishes_item['count']}
                sale_dishes = sale_detail.get(dishes_id, None)
                if not sale_dishes:
                    sale_detail[dishes_id] = sale_tmp
                else:
                    sale_detail[dishes_id]['count'] += dishes_item['count']
            dishes_dict[datetime_day] = sale_detail

        sale_list = []
        for date_key in dishes_dict:
            tmp_list = dishes_dict[date_key].values()
            sale_list.append({'date': str(date_key),
                              'sale_list': sorted(tmp_list, key=lambda x: x['count'], reverse=True)[:6]})
        return sorted(sale_list, key=lambda x: x['date'], reverse=True)


    @classmethod
    def get_sale_list_by_admin(cls, request, **kwargs):
        """
        订单销售统计（管理员）
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
            sale_detail['total_payable'] = Decimal(sale_detail['total_payable']) + \
                                           Decimal(item.payable)
            sale_dict[business_name] = sale_detail
        results = []
        for key, value in sale_dict.items():
            sale_detail = value
            sale_detail['date'] = '%s--%s' % (kwargs.get('start_created',
                                                         sale_detail['start_created']),
                                              kwargs.get('end_created',
                                                         now().date()))
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


class YSPayManager(models.Manager):
    def get(self, *args, **kwargs):
        kwargs['expires__gt'] = now()
        return super(YSPayManager, self).get(*args, **kwargs)

    def filter(self, *args, **kwargs):
        kwargs['expires__gt'] = now()
        return super(YSPayManager, self).filter(*args, **kwargs)


class YinshiPayCode(models.Model):
    """
    吟食支付随机码
    """
    user_id = models.IntegerField('用户ID')
    dishes_ids = models.TextField('订购商品列表')
    pay_orders_id = models.CharField('支付订单ID', max_length=32,
                                     blank=True, null=True, default='')
    consume_orders_id = models.CharField('核销订单ID', max_length=32,
                                         blank=True, null=True, default='')
    code = models.CharField('随机码', max_length=32, db_index=True)
    expires = models.DateTimeField('过期时间', default=minutes_15_plus)
    created = models.DateTimeField('创建日期', default=now)

    objects = YSPayManager()

    class Meta:
        db_table = 'ys_yinshi_pay_code'

    def __unicode__(self):
        return str(self.code)

    @classmethod
    def get_object(cls, **kwargs):
        kwargs = get_perfect_filter_params(cls, **kwargs)
        try:
            return cls.objects.get(**kwargs)
        except Exception as e:
            return e

    @classmethod
    def filter_objects(cls, **kwargs):
        kwargs = get_perfect_filter_params(cls, **kwargs)
        try:
            return cls.objects.filter(**kwargs)
        except Exception as e:
            return e


class PushManager(models.Manager):
    def get(self, *args, **kwargs):
        kwargs['status'] = 0
        kwargs['push_start_time__gt'] = now()
        instance = super(PushManager, self).get(*args, **kwargs)
        return instance

    def filter(self, *args, **kwargs):
        kwargs['status'] = 0
        kwargs['push_start_time__gt'] = now()
        instances = super(PushManager, self).filter(*args, **kwargs)
        return instances


class PushDetail(models.Model):
    """
    推送数据
    """
    business_id = models.IntegerField('商户ID')
    consumer_id = models.IntegerField('用户ID')
    business_name = models.CharField('商户名称', max_length=100)
    food_court_id = models.IntegerField('美食城ID')
    food_court_name = models.CharField('美食城名字', max_length=200)

    out_open_id = models.CharField('第三方唯一标识', max_length=64)
    payable = models.CharField('消费金额', max_length=16)

    created = models.DateTimeField('创建日期', default=now)
    push_start_time = models.DateTimeField('开始推送时间', default=minutes_15_plus)

    # status  0：未推送  1：已推送
    status = models.IntegerField('是否推送标志', db_index=True, default=0)

    objects = PushManager()

    class Meta:
        db_table = 'ys_push_detail'

    def __unicode__(self):
        return str(self.out_open_id)

    @classmethod
    def get_object(cls, **kwargs):
        kwargs = get_perfect_filter_params(cls, **kwargs)
        try:
            return cls.objects.get(**kwargs)
        except Exception as e:
            return e

    @classmethod
    def filter_objects(cls, **kwargs):
        kwargs = get_perfect_filter_params(cls, **kwargs)
        try:
            return cls.objects.filter(**kwargs)
        except Exception as e:
            return e


class PushDetailAction(object):
    """
    创建推送服务
    """
    def create_push_service(self, verify_orders):
        if not isinstance(verify_orders, VerifyOrders):
            return Exception('Data is error.')

        consumer = ConsumerUser.get_object(pk=verify_orders.consumer_id)
        initial_data = {
            'business_id': verify_orders.user_id,
            'consumer_id': verify_orders.consumer_id,
            'business_name': verify_orders.business_name,
            'food_court_id': verify_orders.food_court_id,
            'food_court_name': verify_orders.food_court_name,
            'out_open_id': consumer.out_open_id,
            'payable': verify_orders.payable,
        }

        try:
            instance = PushDetail(**initial_data)
            instance.save()
        except Exception as e:
            return e
        return instance
