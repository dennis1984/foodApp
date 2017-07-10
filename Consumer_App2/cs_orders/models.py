# -*- coding:utf8 -*-
from __future__ import unicode_literals
from django.db import models
from django.utils.timezone import now
from horizon import main


class ConfirmConsumeManager(models.Manager):
    def get(self, *args, **kwargs):
        kwargs['expires__gt'] = now()
        return super(ConfirmConsumeManager, self).get(*args, **kwargs)

    def filter(self, *args, **kwargs):
        kwargs['expires__gt'] = now()
        return super(ConfirmConsumeManager, self).filter(*args, **kwargs)


class ConfirmConsume(models.Model):
    user_id = models.IntegerField('用户ID')
    random_string = models.CharField('随机字符串', db_index=True, max_length=64)
    expires = models.DateTimeField('过期时间', default=main.minutes_5_plus)
    created = models.DateTimeField('创建日期', default=now)

    objects = ConfirmConsumeManager()

    class Meta:
        db_table = 'ys_confirm_consume_qrcode'
        app_label = 'Consumer_App.cs_orders.models.ConfirmConsume'

    def __unicode__(self):
        return str(self.user_id)

    @classmethod
    def get_object(cls, **kwargs):
        try:
            return cls.objects.get(**kwargs)
        except Exception as e:
            return e
