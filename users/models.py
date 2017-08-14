# -*- coding:utf8 -*-
from django.db import models
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser
from django.utils.timezone import now
from django.contrib.auth.hashers import make_password
from oauth2_provider.models import AccessToken
from horizon.models import model_to_dict
from dishes.models import FoodCourt
from django.conf import settings

from horizon import main
from horizon.models import BaseManager
import datetime
import os


ADVERT_OWNER_DICT = {
    'business': 1,
    'consumer': 2,
}


def make_token_expire(request):
    """
    置token过期
    """
    header = request.META
    token = header['HTTP_AUTHORIZATION'].split()[1]
    try:
        _instance = AccessToken.objects.get(token=token)
        _instance.expires = now()
        _instance.save()
    except:
        pass
    return True


class BusinessUserManager(BaseUserManager):
    def create_user(self, username, password, business_name, food_court_id, **kwargs):
        """
        创建商户，
        参数包括：username （手机号）
                 password （长度必须不小于6位）
                 business_name 商户名称（字符串）
                 food_court_id  美食城ID（整数）
        """
        if not username:
            raise ValueError('username cannot be null')

        user = self.model(
            phone=username,
            business_name=business_name,
            food_court_id=food_court_id,
            **kwargs
        )

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password, business_name=None,  food_court_id=None, **kwargs):
        user = self.create_user(username=username,
                                password=password,
                                business_name='admin',
                                food_court_id=0, **kwargs)
        user.is_admin = True
        user.save(using=self._db)
        return user

USER_PICTURE_DIR = settings.PICTURE_DIRS['business']['head_picture']


class BusinessUser(AbstractBaseUser):
    # username = models.CharField(max_length=50, unique=True)
    email = models.EmailField(
        verbose_name='email address',
        max_length=255,
        unique=True,
        null=True,
    )
    business_name = models.CharField(u'商户名称', max_length=100, default='')
    food_court_id = models.IntegerField(u'所属美食城', default=0)
    phone = models.CharField(u'手机号', max_length=20, unique=True, db_index=True)
    brand = models.CharField(u'所属品牌', max_length=60, null=False, default='')
    manager = models.CharField(u'经理人姓名', max_length=20, null=False, default='')
    chinese_people_id = models.CharField(u'身份证号码', max_length=25,
                                         null=False, default='')
    stalls_number = models.CharField(u'档口编号', max_length=20,
                                     null=False, default='')

    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=now)
    head_picture = models.ImageField(u'头像',
                                     upload_to=USER_PICTURE_DIR,
                                     default=os.path.join(USER_PICTURE_DIR, 'noImage.png'), )

    objects = BusinessUserManager()

    USERNAME_FIELD = 'phone'
    REQUIRED_FIELDS = ['business_name']

    class Meta:
        db_table = 'ys_auth_user'
        unique_together = ('business_name', 'food_court_id')

    def set_password(self, raw_password):
        self.password = make_password(raw_password)

    @classmethod
    def get_object(cls, **kwargs):
        try:
            return cls.objects.get(**kwargs)
        except Exception as e:
            return e

    @classmethod
    def get_user_detail(cls, request):
        """
        返回数据结构：
             {'id',             用户ID
             'phone',           手机号
             'business_name',   商户名称
             'food_court_id',   所属美食城ID
             'last_login',      最后登录时间
             'head_picture',    商户头像
             'city',            美食城所在城市
             'district',        美食城所在城市市区
             'food_court_name', 美食城名称
             'mall',            美食城所属购物中心
             }
        """
        try:
            business_user = BusinessUser.objects.get(pk=request.user.id)
        except Exception as e:
            return e
        if request.user.is_admin:
            food_court = {}
        else:
            try:
                food_court = FoodCourt.objects.get(pk=business_user.food_court_id)
            except Exception as e:
                return e

        return cls.join_user_and_food_court(business_user, food_court)

    @classmethod
    def get_objects_list(cls, request, **kwargs):
        """
        获取用户列表
        权限控制：只有管理员可以访问这些数据
        """
        if not request.user.is_admin:
            return Exception('Permission denied, Cannot access the method')

        _kwargs = {}
        if 'start_created' in kwargs:
            _kwargs['created__gte'] = kwargs['start_created']
        if 'end_created' in kwargs:
            _kwargs['created__lte'] = kwargs['end_created']
        _kwargs['is_admin'] = False
        try:
            _instances_list = cls.objects.filter(**_kwargs)
        except Exception as e:
            return e

        results = []
        for _instance in _instances_list:
            try:
                food_court = FoodCourt.objects.get(pk=_instance.food_court_id)
            except Exception as e:
                return e
            user_data = cls.join_user_and_food_court(_instance, food_court)
            results.append(user_data)
        return results

    @classmethod
    def join_user_and_food_court(cls, user_instance, food_court_instance):
        business_user = model_to_dict(user_instance)
        business_user['user_id'] = business_user['id']
        if food_court_instance:
            business_user.update(**model_to_dict(food_court_instance))
            business_user['food_court_name'] = business_user['name']
        # business_user['user_id'] = business_user['id']
        if business_user['last_login'] is None:
            business_user['last_login'] = business_user['date_joined']
        return business_user


class IdentifyingCode(models.Model):
    phone = models.CharField(u'手机号', max_length=20, db_index=True)
    identifying_code = models.CharField(u'手机验证码', max_length=6)
    expires = models.DateTimeField(u'过期时间', default=main.minutes_15_plus)

    class Meta:
        db_table = 'ys_identifying_code'
        ordering = ['-expires']

    def __unicode__(self):
        return self.phone

    @classmethod
    def get_object_by_phone(cls, phone):
        instances = cls.objects.filter(**{'phone': phone, 'expires__gt': now()})
        if instances:
            return instances[0]
        else:
            return None

ADVERT_PICTURE_DIR = settings.PICTURE_DIRS['business']['advert']


class AdvertPictureManager(models.Manager):
    def get(self, *args, **kwargs):
        kwargs.update(**{'status': 1,
                         'owner': ADVERT_OWNER_DICT['business']})
        return super(AdvertPictureManager, self).get(*args, **kwargs)

    def filter(self, *args, **kwargs):
        kwargs.update(**{'status': 1,
                         'owner': ADVERT_OWNER_DICT['business']})
        return super(AdvertPictureManager, self).filter(*args, **kwargs)


class AdvertPicture(models.Model):
    food_court_id = models.IntegerField(u'美食城ID')
    # owner取值： 1: 商户端  2: 用户端
    owner = models.IntegerField(u'广告所属设备端', default=1)
    name = models.CharField(u'图片名称', max_length=60, unique=True, db_index=True)
    image = models.ImageField(u'图片', upload_to=ADVERT_PICTURE_DIR,)
    ad_position_name = models.CharField(u'广告位名称', max_length=60)
    ad_link = models.TextField(u'广告链接')

    # 数据状态：1：有效 2：已删除
    status = models.IntegerField(u'数据状态', default=1)
    created = models.DateTimeField(u'创建时间', default=now)
    updated = models.DateTimeField(u'更新时间', auto_now=True)

    objects = AdvertPictureManager()

    class Meta:
        db_table = 'ys_advert_picture'
        ordering = ['-created']

    def __unicode__(self):
        return self.name

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


class ClientDetail(models.Model):
    """
    客户显示屏信息
    """
    user_id = models.IntegerField(u'用户ID', db_index=True)
    ip = models.CharField(u'IP地址', max_length=40)
    port = models.IntegerField(u'端口')

    # 数据状态：1：有效 2：已删除
    status = models.IntegerField(u'数据状态', default=1)
    created = models.DateTimeField(u'创建时间', default=now)
    updated = models.DateTimeField(u'更新时间', auto_now=True)

    objects = BaseManager()

    class Meta:
        db_table = 'ys_client_detail'
        ordering = ['-created']

    def __unicode__(self):
        return unicode(self.user_id)

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

    @classmethod
    def get_object_by_user(cls, request):
        instances = cls.filter_objects(user_id=request.user.id)
        if isinstance(instances, Exception):
            return instances
        if len(instances) == 0:
            return None
        return instances[0]

