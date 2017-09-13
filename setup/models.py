# -*- coding:utf8 -*-
from __future__ import unicode_literals

from django.db import models
from django.utils.timezone import now
from django.conf import settings
from horizon.models import BaseManager
import os
import json

PACKAGE_DIR = settings.PICTURE_DIRS['business']['app_package']


class AppVersion(models.Model):
    """
    App版本信息
    """
    version_name = models.CharField('版本号名称', max_length=16)
    version_code = models.IntegerField('版本号', default=0)
    message = models.CharField('版本描述信息', max_length=256)
    is_force_update = models.BooleanField('是否强制更新', default=False)

    package_path = models.FileField('App包存放目录',
                                    upload_to=PACKAGE_DIR)
    # 数据状态：1：正常，其他：已删除
    status = models.IntegerField('数据状态', default=1)
    created = models.DateTimeField('创建时间', default=now)
    updated = models.DateTimeField('最后修改时间', auto_now=True)

    objects = BaseManager()

    class Meta:
        db_table = 'ys_app_version'
        unique_together = ['version_name', 'version_code', 'status']
        ordering = ['-updated']

    def __unicode__(self):
        return '%s.%s' % (self.version_name, self.version_code)

    @classmethod
    def get_object(cls, **kwargs):
        try:
            return cls.objects.get(**kwargs)
        except Exception as e:
            return e

    @classmethod
    def get_last_version(cls):
        instances = cls.filter_objects()
        if isinstance(instances, Exception):
            return instances
        if instances.count() == 0:
            return Exception('Version data does not exist.')
        return instances[0]

    @classmethod
    def filter_objects(cls, **kwargs):
        try:
            return cls.objects.filter(**kwargs)
        except Exception as e:
            return e

