# -*- coding:utf8 -*-
from __future__ import unicode_literals
import json
import datetime

from django.conf import settings
from horizon import redis
from django.utils.timezone import now

from dishes.models import Dishes, DISHES_MARK_DISCOUNT_VALUES
from orders.models import Orders


# 过期时间（单位：秒）
EXPIRE_SECONDS = 10 * 60 * 60
EXPIRE_24_HOURS = 24 * 60 * 60


class DishesCache(object):
    def __init__(self):
        pool = redis.ConnectionPool(host=settings.REDIS_SETTINGS['host'],
                                    port=settings.REDIS_SETTINGS['port'],
                                    db=settings.REDIS_SETTINGS['db_set']['business'])
        self.handle = redis.Redis(connection_pool=pool)

    def set_dishes_list(self, request, dishes_list):
        key = self.get_dishes_list_key(request=request)
        self.handle.delete(key)
        self.handle.rpush(key, *dishes_list)
        self.handle.expire(key, EXPIRE_SECONDS)

    def get_dishes_list(self, request, **kwargs):
        key = self.get_dishes_list_key(request)
        dishes_list = self.handle.lrange(key)
        if not dishes_list:
            _dishes_list = Dishes.get_object_list(request, **kwargs)
            # 用最近一个月的菜品销量来排序商户的菜品列表
            orders_filter = {'start_created': now() - datetime.timedelta(days=30),
                             'payment_status': 200}
            orders_list = Orders.get_objects_list(request, **orders_filter)
            sale_list = self.get_dishes_list_with_sale(dishes_list=_dishes_list,
                                                       orders_list=orders_list)
            self.set_dishes_list(request, sale_list)
            return sale_list
        return dishes_list

    def get_dishes_list_key(self, request):
        return 'dishes_list_key:%s' % request.user.id

    def delete_dishes_list(self, request):
        key = self.get_dishes_list_key(request)
        self.handle.delete(key)

    @classmethod
    def get_dishes_list_with_sale(cls, dishes_list, orders_list):
        sale_list = []
        sale_dict = {}
        for item in orders_list:
            dishes_ids = json.loads(item.dishes_ids)
            for dishes_item in dishes_ids:
                pk = dishes_item['id']
                sale_dict[pk] = dishes_item['count'] + sale_dict.get(pk, 0)

        dishes_dict = {item.id: item for item in dishes_list}
        for key, value in sorted(sale_dict.items(), key=lambda x: x[1], reverse=True):
            if key in dishes_dict:
                sale_list.append(dishes_dict.pop(key))
        if dishes_dict:
            sale_list.extend(sorted(dishes_dict.values(), key=lambda x: x.created, reverse=True))
        return sale_list


class ConsumerHotSaleCache(object):
    def __init__(self):
        pool = redis.ConnectionPool(host=settings.REDIS_SETTINGS['host'],
                                    port=settings.REDIS_SETTINGS['port'],
                                    db=settings.REDIS_SETTINGS['db_set']['consumer'])
        self.handle = redis.Redis(connection_pool=pool)

    def get_hot_sale_list_key(self, food_court_id=1, mark=10):
        return 'hot_sale_id_key:food_court_id:%s:mark:%s' % (food_court_id, mark)

    def delete_data_from_cache(self, food_court_id):
        for mark_id in (DISHES_MARK_DISCOUNT_VALUES + [0]):
            key = self.get_hot_sale_list_key(food_court_id, mark_id)
            self.handle.delete(key)
