#-*- coding:utf8 -*-
from django.db import models
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser
from django.utils.timezone import now
from django.contrib.auth.hashers import make_password


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



