# -*- coding:utf8 -*-

from rest_framework import serializers
from django.utils.timezone import now
from django.conf import settings

from horizon.main import make_random_string_char_and_number
from horizon.serializers import (BaseModelSerializer,
                                 BaseListSerializer,
                                 BaseSerializer)
from dishes.models import (Dishes,
                           FoodCourt,
                           DISHES_SIZE_CN_MATCH,
                           DISHES_SIZE_DICT)
from dishes.caches import DishesCache

import datetime
import json


def make_cache_expired(func):
    def decorator(self, request, *args, **kwargs):
        result = func(self, request, *args, **kwargs)
        DishesCache().delete_dishes_list(request)
        return result
    return decorator


class DishesSerializer(BaseModelSerializer):
    def __init__(self, instance=None, data=None, request=None, **kwargs):
        if data and request:
            data['user_id'] = request.user.id
            data['food_court_id'] = request.user.food_court_id
            size = data.get('size', 10)
            if size != DISHES_SIZE_DICT['custom']:
                data['size_detail'] = DISHES_SIZE_CN_MATCH[size]

            # 处理管理后台上传图片图片名字没有后缀的问题
            if 'image' in data:
                image_names = data['image'].name.split('.')
                if len(image_names) == 1:
                    data['image'].name = '%s.png' % image_names[0]
            super(DishesSerializer, self).__init__(data=data, **kwargs)
        else:
            super(DishesSerializer, self).__init__(instance, **kwargs)

    class Meta:
        model = Dishes
        fields = '__all__'

    @make_cache_expired
    def save(self, request, **kwargs):
        try:
            return super(DishesSerializer, self).save(**kwargs)
        except Exception as e:
            return e

    @make_cache_expired
    def delete(self, request, obj):
        validated_data = {'status': 2,
                          'size_detail': '%s-%s' % (obj.size_detail,
                                                    make_random_string_char_and_number(8))}
        return super(DishesSerializer, self).update(obj, validated_data)

    @make_cache_expired
    def update_dishes(self, request, instance, validated_data):
        """
        权限控制：1. 只有管理员能设置is_recommend字段
                2. 只有创建者能修改自己创建的数据
        """
        if 'is_recommend' in validated_data and not request.user.is_admin:
            raise Exception('Permission denied')
        elif request.user.id != instance.user_id:
            raise Exception('Permission denied')
        if 'pk' in validated_data:
            validated_data.pop('pk')
        if 'size' in validated_data:
            size = validated_data['size']
            if size != DISHES_SIZE_DICT['custom']:
                validated_data['size_detail'] = DISHES_SIZE_CN_MATCH[size]
        return super(DishesSerializer, self).update(instance, validated_data)


class DishesListSerializer(BaseListSerializer):
    child = DishesSerializer()


class FoodCourtSerializer(BaseModelSerializer):
    class Meta:
        model = FoodCourt
        fields = '__all__'


class FoodCourtListSerializer(BaseListSerializer):
    child = FoodCourtSerializer()
