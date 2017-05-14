# -*- coding:utf8 -*-
from __future__ import unicode_literals

from django.db import models
from django.utils.timezone import now


class DishesManager(models.Manager):
    def get_query_set(self, *args, **kwargs):
        object_data = super(DishesManager, self).get_query_set().filter(status=1, *args, **kwargs)
        object_data.created = str(object_data.created)
        object_data.updated = str(object_data.updated)
        return object_data


class Dishes(models.Model):
    # dishes_id = models.IntegerField('菜品ID', unique=True, null=False)
    title = models.CharField('菜品名称', db_index=True, null=False, max_length=200)
    subtitle = models.CharField('菜品副标题', max_length=200, default='')
    description = models.TextField('菜品描述', default='')
    price = models.CharField('价格', max_length=50, null=False)
    image_url = models.URLField('菜品图片链接', max_length=500, default='', blank=True)
    user_id = models.IntegerField('创建者ID', null=False)
    created = models.DateTimeField('创建时间', default=now)
    updated = models.DateTimeField('最后修改时间', auto_now=True)
    status = models.IntegerField('数据状态', default=1)   # 1 有效 2 已删除 3 其他（比如暂时不用）
    extend = models.TextField('扩展信息', default='', blank=True)

    objects = models.Manager()
    active_objects = DishesManager()

    class Meta:
        db_table = 'ys_dishes'


class Meal_center(models.Model):
    center_id = models.IntegerField('美食城ID', unique=True, null=False)
    center_name = models.CharField('美食城名字', max_length=200)
    city = models.CharField('所属城市', max_length=100, null=False)
    city_area = models.CharField('所属市区', max_length=100, null=False)
    mall = models.CharField('所属购物中心', max_length=200, default='')

    class Meta:
        db_table = 'ys_meal_center'





