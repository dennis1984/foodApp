#-*- coding:utf8 -*-
from dishes.models import Dishes, FoodCourt
from rest_framework import serializers
from django.core.paginator import Paginator
from django.conf import settings
from horizon.serializers import BaseListSerializer, timezoneStringTostring
import datetime, os
from dishes.caches import DishesCache


def make_cache_expired(func):
    def decorator(self, request, *args, **kwargs):
        result = func(self, request, *args, **kwargs)
        DishesCache().delete_dishes_list(request)
        return result
    return decorator


class DishesSerializer(serializers.ModelSerializer):
    def __init__(self, *args, **kwargs):
        if '_request' in kwargs:
            request = kwargs['_request']
            data = request.data.copy()
            data['user_id'] = request.user.id

            # 处理管理后台上传图片图片名字没有后缀的问题
            if 'image' in data:
                image_names = data['image'].name.split('.')
                if len(image_names) == 1:
                    data['image'].name = '%s.png' % image_names[0]
            super(DishesSerializer, self).__init__(data=data)
        else:
            super(DishesSerializer, self).__init__(*args, **kwargs)

    class Meta:
        model = Dishes
        # fields = ('dishes_id', 'title', 'subtitle', 'description',
        #           'price', 'image_url', 'user_id', 'extend')
        fields = '__all__'

    @make_cache_expired
    def save(self, request, **kwargs):
        return super(DishesSerializer, self).save(**kwargs)

    @make_cache_expired
    def delete(self, request, obj):
        validated_data = {'status': 2}
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
        return super(DishesSerializer, self).update(instance, validated_data)

    @property
    def data(self):
        serializer = super(DishesSerializer, self).data
        if serializer.get('user_id', None):
            serializer['updated'] = timezoneStringTostring(serializer['updated'])
            serializer['created'] = timezoneStringTostring(serializer['created'])
            serializer['image_url'] = os.path.join(settings.WEB_URL_FIX, serializer['image'])
        return serializer


class DishesListSerializer(BaseListSerializer):
    child = DishesSerializer()


class FoodCourtSerializer(serializers.ModelSerializer):
    class Meta:
        model = FoodCourt
        fields = '__all__'


class FoodCourtListSerializer(BaseListSerializer):
    child = FoodCourtSerializer()
