# -*- coding:utf8 -*-
from __future__ import unicode_literals

from django.db import models
from django.utils.timezone import now
from django.conf import settings
import os
import json


class DishesManager(models.Manager):
    def get(self, *args, **kwargs):
        object_data = super(DishesManager, self).get(status=1, *args, **kwargs)
        return object_data

    def filter(self, *args, **kwargs):
        object_data = super(DishesManager, self).filter(status=1, *args, **kwargs)
        return object_data


DISHES_PICTURE_DIR = settings.PICTURE_DIRS['business']['dishes']
FOOD_COURT_DIR = settings.PICTURE_DIRS['business']['food_court']

DISHES_SIZE_DICT = {
    'default': 10,
    'small': 11,
    'medium': 12,
    'large': 13,
    'custom': 20,
}

DISHES_SIZE_CN_MATCH = {
    10: u'标准',
    11: u'小份',
    12: u'中份',
    13: u'大份',
    20: u'自定义',
}


class Dishes(models.Model):
    """
    菜品信息表
    """
    title = models.CharField('菜品名称', null=False, max_length=40)
    subtitle = models.CharField('菜品副标题', max_length=100, default='')
    description = models.TextField('菜品描述', default='')
    # 默认：10，小份：11，中份：12，大份：13，自定义：20
    size = models.IntegerField('菜品规格', default=10)
    size_detail = models.CharField('菜品规格详情', max_length=30, null=True, blank=True)
    price = models.CharField('价格', max_length=16, null=False, blank=False)
    image = models.ImageField('菜品图片（封面）',
                              upload_to=DISHES_PICTURE_DIR,
                              default=os.path.join(DISHES_PICTURE_DIR, 'noImage.png'), )
    image_detail = models.ImageField('菜品图片（详情）',
                                     upload_to=DISHES_PICTURE_DIR,
                                     default=os.path.join(DISHES_PICTURE_DIR, 'noImage.png'), )
    user_id = models.IntegerField('创建者ID', db_index=True)
    food_court_id = models.IntegerField('商城ID', db_index=True)
    created = models.DateTimeField('创建时间', default=now)
    updated = models.DateTimeField('最后修改时间', auto_now=True)
    status = models.IntegerField('数据状态', default=1)   # 1 有效 2 已删除 3 其他（比如暂时不用）
    is_recommend = models.BooleanField('是否推荐该菜品', default=False)   # 0: 不推荐  1：推荐
    extend = models.TextField('扩展信息', default='', null=True, blank=True)

    objects = DishesManager()

    class Meta:
        db_table = 'ys_dishes'
        unique_together = ('user_id', 'title', 'size',
                           'size_detail', 'status')

    def __unicode__(self):
        return self.title

    @classmethod
    def get_object(cls, **kwargs):
        try:
            return cls.objects.get(**kwargs)
        except Exception as e:
            return e

    @classmethod
    def get_object_list(cls, request, **kwargs):
        # 如果是用户是admin并且过滤条件为空，则返回所有菜品
        # 否则返回过滤条件中对应用户的所有菜品
        # 如果是商户，则返回当前用户的所有菜品
        if request.user.is_admin:
            if 'user_id' not in kwargs:
                return cls.objects.all()
            else:
                filter_dict = {'user_id': kwargs['user_id']}
        else:
            filter_dict = {'user_id': request.user.id}

        try:
            return cls.objects.filter(**filter_dict)
        except Exception as e:
            return e


class FoodCourt(models.Model):
    """
    美食城数据表
    """
    name = models.CharField('美食城名字', max_length=200)
    # 美食城类别 10: 公元铭 20：食代铭
    type = models.IntegerField('美食城类别', default=10)
    city = models.CharField('所属城市', max_length=100, null=False)
    district = models.CharField('所属市区', max_length=100, null=False)
    mall = models.CharField('所属购物中心', max_length=200, default='')
    address = models.CharField('购物中心地址', max_length=256, null=True, blank=True)
    image = models.ImageField('美食城平面图',
                              upload_to=FOOD_COURT_DIR,
                              default=os.path.join(FOOD_COURT_DIR, 'noImage.png'),)
    # 状态：1：有效 2：已删除
    status = models.IntegerField('数据状态', default=1)
    extend = models.TextField('扩展信息', default='', blank=True, null=True)

    class Meta:
        db_table = 'ys_food_court'
        unique_together = ('name', 'mall', 'status')

    def __unicode__(self):
        return self.name

    @classmethod
    def get_object(cls, **kwargs):
        try:
            return cls.objects.get(**kwargs)
        except Exception as e:
            return e

    @classmethod
    def get_object_list(cls, **kwargs):
        if 'page_size' in kwargs:
            kwargs.pop('page_size')
        if 'page_index' in kwargs:
            kwargs.pop('page_index')
        return cls.objects.filter(**kwargs)


class City(models.Model):
    """
    城市信息
    """
    city = models.CharField('城市名称', max_length=40, db_index=True)
    # 市区数据结构：
    # [{'id': 1, 'name': u'大兴区'}, ...
    # ]
    district = models.CharField('市区信息', max_length=40)

    user_id = models.IntegerField('创建者')
    # 状态：1：有效 2：已删除
    status = models.IntegerField('数据状态', default=1)
    created = models.DateTimeField(default=now)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'ys_city'
        unique_together = ('city', 'status')
        ordering = ['-updated']

    def __unicode__(self):
        return self.city

    @classmethod
    def get_object(cls, **kwargs):
        try:
            return cls.objects.get(**kwargs)
        except Exception as e:
            return e
