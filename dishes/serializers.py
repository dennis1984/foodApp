#-*- coding:utf8 -*-
from dishes.models import Dishes, FoodCourt
from rest_framework import serializers
from django.shortcuts import render, redirect
from django.core.urlresolvers import reverse
import datetime


class DishesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dishes
        # fields = ('dishes_id', 'title', 'subtitle', 'description',
        #           'price', 'image_url', 'user_id', 'extend')
        fields = '__all__'

    def delete(self, obj):
        validated_data = {'status': 2}
        super(DishesSerializer, self).update(obj, validated_data)


class DishesInitSerializer(DishesSerializer):
    def __init__(self, data, request, **kwargs):
        data['user_id'] = request.user.id
        super(DishesInitSerializer, self).__init__(data=data, **kwargs)


class DishesResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dishes
        fields = '__all__'
        # fields = ('id', 'title', 'subtitle', 'description',
        #           'price', 'image_url', 'user_id', 'extend')

    @property
    def data(self):
        serializer = super(DishesResponseSerializer, self).data
        if serializer.get('user_id', None):
            serializer['updated'] = timezoneStringTostring(serializer['updated'])
            serializer['created'] = timezoneStringTostring(serializer['created'])
            serializer['image_url'] = serializer['image']
        return serializer


class FoodCourtSerializer(serializers.ModelSerializer):
    class Meta:
        model = FoodCourt
        fields = '__all__'


def timezoneStringTostring(timezone_string):
    """
    rest framework用JSONRender方法格式化datetime.datetime格式的数据时，
    生成数据样式为：2017-05-19T09:40:37.227692Z 或 2017-05-19T09:40:37Z
    此方法将数据样式改为："2017-05-19 09:40:37"，
    返回类型：string
    """
    timezone_string = timezone_string.split('.')[0]
    timezone_string = timezone_string.split('Z')[0]
    timezone = datetime.datetime.strptime(timezone_string, '%Y-%m-%dT%H:%M:%S')
    return str(timezone)

