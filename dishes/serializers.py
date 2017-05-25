#-*- coding:utf8 -*-
from dishes.models import Dishes, FoodCourt
from rest_framework import serializers
from django.core.paginator import Paginator
from django.conf import settings
from horizon.serializers import BaseListSerializer, timezoneStringTostring
import datetime, os


class DishesSerializer(serializers.ModelSerializer):
    def __init__(self, *args, **kwargs):
        if '_request' in kwargs:
            request = kwargs['_request']
            data = request.data.copy()
            data['user_id'] = request.user.id
            super(DishesSerializer, self).__init__(data=data)
        else:
            super(DishesSerializer, self).__init__(*args, **kwargs)

    class Meta:
        model = Dishes
        # fields = ('dishes_id', 'title', 'subtitle', 'description',
        #           'price', 'image_url', 'user_id', 'extend')
        fields = '__all__'

    def delete(self, obj):
        validated_data = {'status': 2}
        super(DishesSerializer, self).update(obj, validated_data)

    def update_dishes(self, request, instance, validated_data):
        """
        权限控制，只有管理员能设置is_recommend字段
        """
        if 'is_recommend' in validated_data and not request.user.is_admin:
            raise Exception('Permission denied')
        return super(DishesSerializer, self).update(instance, validated_data)

    @property
    def data(self):
        serializer = super(DishesSerializer, self).data
        if serializer.get('user_id', None):
            serializer['updated'] = timezoneStringTostring(serializer['updated'])
            serializer['created'] = timezoneStringTostring(serializer['created'])
            serializer['image_url'] = os.path.join(settings.DOMAIN_NAME, serializer['image'])
        return serializer


class DishesListSerializer(BaseListSerializer):
    child = DishesSerializer()


class FoodCourtSerializer(serializers.ModelSerializer):
    class Meta:
        model = FoodCourt
        fields = '__all__'


class FoodCourtListSerializer(BaseListSerializer):
    child = FoodCourtSerializer()
