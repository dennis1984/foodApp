# -*- coding:utf8 -*-
from __future__ import unicode_literals
import json
import datetime

from django.conf import settings
from horizon import redis
from django.utils.timezone import now

from users.models import BusinessUser, ClientDetail


# 过期时间（单位：秒）
EXPIRES_24_HOURS = 24 * 60 * 60
EXPIRES_10_HOURS = 10 * 60 * 60


class BusinessUserCache(object):
    def __init__(self):
        pool = redis.ConnectionPool(host=settings.REDIS_SETTINGS['host'],
                                    port=settings.REDIS_SETTINGS['port'],
                                    db=settings.REDIS_SETTINGS['db_set']['business'])
        self.handle = redis.Redis(connection_pool=pool)

    def get_user_id_key(self, user_id):
        return 'user_instance_id:%s' % user_id

    def get_user_name_key(self, user_name):
        return 'user_instance_phone:%s' % user_name

    def get_client_ip_port_by_user_id_key(self, user_id):
        return 'client_ip_port:user_id:%s' % user_id

    def set_data_to_cache(self, key, data):
        self.handle.set(key, data)
        self.handle.expire(key, EXPIRES_24_HOURS)

    def get_data_from_cache(self, key):
        return self.handle.get(key)

    def delete_data_from_cache(self, key):
        return self.handle.delete(key)

    def get_user_by_id(self, request, user_id=None):
        if not request.user.is_admin:
            user_id = request.user.id
        key = self.get_user_id_key(user_id)
        user_instance = self.handle.get(key)
        if not user_instance:
            user_instance = BusinessUser.get_object(**{'pk': user_id})
            if isinstance(user_instance, Exception):
                return user_instance
            self.set_data_to_cache(key, user_instance)
        return user_instance

    def get_user_by_username(self, user_name):
        key = self.get_user_name_key(user_name)
        user_instance = self.handle.get(key)
        if not user_instance:
            user_instance = BusinessUser.get_object(**{'phone': user_name})
            if isinstance(user_instance, Exception):
                return user_instance
            self.set_data_to_cache(key, user_instance)
        return user_instance

    def get_client_ip_port_data(self, user_id):
        key = self.get_client_ip_port_by_user_id_key(user_id)
        data = self.get_data_from_cache(key)
        if not data:
            data = ClientDetail.get_object_by_user(user_id)
            if isinstance(data, Exception):
                return data
            self.set_data_to_cache(key, data)
        return data

    def delete_client_ip_port_data(self, user_id):
        key = self.get_client_ip_port_by_user_id_key(user_id)
        return self.delete_data_from_cache(key)
