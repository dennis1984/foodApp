# -*- coding:utf8 -*-
from __future__ import unicode_literals

from django.db import models
from django.utils.timezone import now


class DishesManager(models.Manager):
    def get(self, *args, **kwargs):
        object_data = super(DishesManager, self).get(status=1, *args, **kwargs)
        return object_data

    def filter(self, *args, **kwargs):
        object_data = super(DishesManager, self).filter(status=1, *args, **kwargs)
        return object_data


class Dishes(models.Model):
    """
    菜品信息表
    """
    title = models.CharField('菜品名称', db_index=True, null=False, max_length=200)
    subtitle = models.CharField('菜品副标题', max_length=200, default='')
    description = models.TextField('菜品描述', default='')
    price = models.CharField('价格', max_length=50, null=False)
    image = models.ImageField('菜品图片', upload_to='static/picture/',
                              default='static/picture/noImage.png', null=True)
    user_id = models.IntegerField('创建者ID', null=False)
    created = models.DateTimeField('创建时间', default=now)
    updated = models.DateTimeField('最后修改时间', auto_now=True)
    status = models.IntegerField('数据状态', default=1)   # 1 有效 2 已删除 3 其他（比如暂时不用）
    extend = models.TextField('扩展信息', default='', blank=True)

    # objects = models.Manager()
    # active_objects = DishesManager()
    objects = DishesManager()

    class Meta:
        db_table = 'ys_dishes'
        unique_together = ('title', 'user_id')

    def __unicode__(self):
        return self.title

    @classmethod
    def get_object(cls, **kwargs):
        try:
            return cls.objects.get(**kwargs)
        except Exception as e:
            return e


class FoodCourt(models.Model):
    """
    美食城数据表
    """
    name = models.CharField('美食城名字', max_length=200)
    city = models.CharField('所属城市', max_length=100, null=False)
    district = models.CharField('所属市区', max_length=100, null=False)
    mall = models.CharField('所属购物中心', max_length=200, default='')
    extend = models.TextField('扩展信息', default='', blank=True, null=True)

    class Meta:
        db_table = 'ys_food_court'
        unique_together = ('name', 'mall')

    @classmethod
    def get_object(cls, **kwargs):
        try:
            return cls.objects.get(**kwargs)
        except Exception as e:
            return e
