#-*- coding:utf8 -*-
from django.db import models
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser
from django.utils.timezone import now
from django.contrib.auth.hashers import make_password
from horizon.models import model_to_dict
from dishes.models import FoodCourt
import datetime


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
    head_picture = models.ImageField(u'头像', upload_to='static/picture/head_picture/',
                                     default='static/picture/head_picture/noImage.png', null=True)

    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=now)

    # create_objects = BusinessUserManager()
    # objects = BaseUserManager()
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
        except cls.DoesNotExist:
            return None

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
        business_user.update(**model_to_dict(food_court_instance))
        business_user['food_court_name'] = business_user['name']
        business_user['user_id'] = business_user['id']
        if business_user['last_login'] is None:
            business_user['last_login'] = business_user['date_joined']
        return business_user

