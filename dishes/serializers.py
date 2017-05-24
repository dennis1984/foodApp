#-*- coding:utf8 -*-
from dishes.models import Dishes, FoodCourt
from rest_framework import serializers
from django.core.paginator import Paginator
from django.conf import settings
from horizon.serializers import BaseListSerializer, timezoneStringTostring
import datetime


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

    @property
    def data(self):
        serializer = super(DishesSerializer, self).data
        if serializer.get('user_id', None):
            serializer['updated'] = timezoneStringTostring(serializer['updated'])
            serializer['created'] = timezoneStringTostring(serializer['created'])
            serializer['image_url'] = serializer['image']
        return serializer


class DishesListSerializer(BaseListSerializer):
    child = DishesSerializer()


class FoodCourtSerializer(serializers.ModelSerializer):
    class Meta:
        model = FoodCourt
        fields = '__all__'


class FoodCourtListSerializer(BaseListSerializer):
    child = FoodCourtSerializer()
