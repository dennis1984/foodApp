# -*- coding:utf8 -*-
from __future__ import unicode_literals

from django.db import models
from django.utils.timezone import now
from django.conf import settings

from horizon.models import get_perfect_filter_params, model_to_dict

import os
import json

from horizon.models import BaseManager

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
DISHES_MARK = {
    'default': 0,
    'new': 10,
    'preferential': 20,
    'flagship': 30,
    'new_business': 40,
    'night_discount': 50,
}
DISHES_MARK_DISCOUNT_VALUES = (10, 20, 30, 40, 50)
CAN_NOT_USE_COUPONS_WITH_MARK = [DISHES_MARK['new_business']]
DISHES_PICTURE_DIR = settings.PICTURE_DIRS['business']['dishes']
FOOD_COURT_DIR = settings.PICTURE_DIRS['business']['food_court']


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

    # 运营标记： 0：无标记  10：新品  20：特惠  30：招牌  40: 新商户专区  50: 晚市特惠
    mark = models.IntegerField('运营标记', default=0)
    # 优惠金额
    discount = models.CharField('优惠金额', max_length=16, default='0')
    # 优惠时间段-开始 (用来标记菜品在某个时段是否有优惠)，以24小时制数字为标准， 如：8:00（代表早晨8点）
    discount_time_slot_start = models.CharField('优惠时间段-开始', max_length=16, null=True)
    # 优惠时间段-结束 (用来标记菜品在某个时段是否有优惠)，以24小时制数字为标准， 如：19:30（代表晚上7点30分）
    discount_time_slot_end = models.CharField('优惠时间段-结束', max_length=16, null=True)

    # 菜品标记和排序顺序
    tag = models.CharField('标记', max_length=64, default='', null=True, blank=True)
    sort_orders = models.IntegerField('排序标记', default=None,  null=True)
    # 菜品类别:  0: 默认
    classify = models.IntegerField('菜品类别', default=0)

    extend = models.TextField('扩展信息', default='', null=True, blank=True)

    objects = BaseManager()

    class Meta:
        db_table = 'ys_dishes'
        unique_together = ('user_id', 'title', 'size',
                           'size_detail', 'status')
        ordering = ['-updated']

    def __unicode__(self):
        return self.title

    @property
    def perfect_data(self):
        detail = model_to_dict(self)
        dishes_classify = DishesClassify.get_object(pk=self.classify)
        if isinstance(dishes_classify):
            detail['classify_name'] = ''
        else:
            detail['classify_name'] = dishes_classify.name
        return detail

    @classmethod
    def get_object(cls, **kwargs):
        kwargs = get_perfect_filter_params(cls, **kwargs)
        try:
            return cls.objects.get(**kwargs)
        except Exception as e:
            return e

    @classmethod
    def get_detail(cls, **kwargs):
        instance = cls.get_object(**kwargs)
        if isinstance(instance, Exception):
            return instance
        return instance.perfect_data
    
    @classmethod
    def get_object_list(cls, request, **kwargs):
        kwargs = get_perfect_filter_params(cls, **kwargs)
        kwargs.update(**{'user_id': request.user.id})
        try:
            return cls.objects.filter(**kwargs)
        except Exception as e:
            return e

    @classmethod
    def filter_details(cls, request, **kwargs):
        instances = cls.get_object_list(request, **kwargs)
        if isinstance(instances, Exception):
            return instances
        details = []
        for ins in instances:
            details.append(ins.perfect_data)
        return details


class DishesClassify(models.Model):
    """
    菜品分类信息表
    """
    name = models.CharField('类别名称', max_length=64, db_index=True)
    description = models.CharField('类别描述', max_length=256, null=True, blank=True)
    user_id = models.IntegerField('用户ID')
    # 状态：1：有效 非1：已删除
    status = models.IntegerField('数据状态', default=1)
    created = models.DateTimeField('创建时间', default=now)
    updated = models.DateTimeField('更新时间', auto_now=True)

    objects = BaseManager()

    class Meta:
        db_table = 'ys_dishes_classify'
        unique_together = ('user_id', 'name', 'status')
        ordering = ('name',)

    @classmethod
    def get_object(cls, **kwargs):
        try:
            return cls.objects.get(**kwargs)
        except Exception as e:
            return e

    @classmethod
    def filter_objects(cls, **kwargs):
        try:
            return cls.objects.filter(**kwargs)
        except Exception as e:
            return e


class FoodCourt(models.Model):
    """
    美食城数据表
    """
    name = models.CharField('美食城名字', max_length=200, db_index=True)
    # 美食城类别 10: 公元铭 20：食代铭
    type = models.IntegerField('美食城类别', default=10)
    city_id = models.IntegerField('所属城市ID')
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

    objects = BaseManager()

    class Meta:
        db_table = 'ys_food_court'
        unique_together = ('name', 'mall', 'city_id', 'status')
        ordering = ['city', 'district']

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

    objects = BaseManager()

    class Meta:
        db_table = 'ys_city'
        unique_together = ('city', 'district', 'status')
        ordering = ['city', 'district']

    def __unicode__(self):
        return self.city

    @classmethod
    def get_object(cls, **kwargs):
        try:
            return cls.objects.get(**kwargs)
        except Exception as e:
            return e

#
# class DishesExtend(models.Model):
#     """
#     菜品信息扩展
#     """
#     dishes_id = models.IntegerField('菜品ID', db_index=True, unique=True)
#     tag = models.CharField('标记', max_length=64, default='', null=True, blank=True)
#     sort_orders = models.IntegerField('排序标记', null=True)
#
#     created = models.DateTimeField('创建时间', default=now)
#     updated = models.DateTimeField('更新时间', auto_now=True)
#
#     class Meta:
#         db_table = 'ys_dishes_extend'
