# -*- coding:utf8 -*-
from django.db import models
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser
from django.utils.timezone import now
from django.conf import settings
import os


class ConsumerUserManager(BaseUserManager):
    pass

HEAD_PICTURE_PATH = settings.PICTURE_DIRS['consumer']['head_picture']


class ConsumerUser(AbstractBaseUser):
    phone = models.CharField(u'手机号', max_length=20, unique=True, db_index=True,
                             null=True)
    out_open_id = models.CharField(u'第三方唯一标识', max_length=64, unique=True,
                                   db_index=True, null=True)
    nickname = models.CharField(u'昵称', max_length=100, null=True, blank=True)

    # 性别，0：未设定，1：男，2：女
    gender = models.IntegerField(u'性别', default=0)
    birthday = models.DateField(u'生日', null=True)
    province = models.CharField(u'所在省份或直辖市', max_length=16, null=True, blank=True)
    city = models.CharField(u'所在城市', max_length=32, null=True, blank=True)
    head_picture = models.ImageField(u'头像', max_length=200,
                                     upload_to=HEAD_PICTURE_PATH,
                                     default=os.path.join(HEAD_PICTURE_PATH, 'noImage.png'))

    # 注册渠道：客户端：YS，微信第三方：WX，QQ第三方：QQ，淘宝：TB
    #          新浪微博：SINA_WB
    channel = models.CharField(u'注册渠道', max_length=20, default='YS')
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)
    date_joined = models.DateTimeField(u'创建时间', default=now)
    updated = models.DateTimeField(u'最后更新时间', auto_now=True)

    objects = ConsumerUserManager()

    USERNAME_FIELD = 'phone'
    REQUIRED_FIELDS = ['channel']

    class Meta:
        db_table = 'ys_auth_user'
        # unique_together = ('nickname', 'food_court_id')
        app_label = 'Consumer_App.cs_users.models.ConsumerUser'

    def __unicode__(self):
        return self.phone

    @classmethod
    def get_object(cls, **kwargs):
        try:
            return cls.objects.get(**kwargs)
        except cls.DoesNotExist as e:
            return Exception(e)


class WXAPPInformation(models.Model):
    app_id = models.CharField(u'开发者ID（APPID）', max_length=32)
    app_secret = models.CharField(u'开发者秘钥（APPSECRET）', max_length=64)
    created = models.DateTimeField(u'创建时间', default=now)

    class Meta:
        db_table = 'ys_wx_app_information'
        app_label = 'Consumer_App.cs_users.models.ys_wx_app_information'

    def __unicode__(self):
        return self.app_id

    @classmethod
    def get_object(cls):
        try:
            return cls.objects.all()[0]
        except Exception as e:
            return e
