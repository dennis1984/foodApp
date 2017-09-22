# -*- coding:utf8 -*-
"""
Django settings for foodApp project.

Generated by 'django-admin startproject' using Django 1.11.

For more information on this file, see
https://docs.djangoproject.com/en/1.11/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.11/ref/settings/
"""

import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.11/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '*h0)(5do!am4we9sx#p&x5tu925vz@4)^4-70l-lqowfnc=aq-'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = ['*']

# 服务器环境（根据服务器环境不同，配置不同的值）
ENVIRONMENT_DICT = {
    'DEV': 10,        # 开发环境
    'TEST': 20,       # 测试环境
    'PRODUCE': 30,    # 生产环境
}
ENVIRONMENT = 10

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    # 'rest_framework.authtoken',
    'oauth2_provider',
    'orders',
    'dishes',
    'users',
    'PAY.wxpay',
    'PAY.alipay',
    'wallet',
    'setup',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'foodApp.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'foodApp.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.11/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'yinShi',
        'USER': 'yinShi_project',
        'PASSWORD': 'Con!082%Trib',
        'HOST': '127.0.0.1',
        'PORT': 3306,
    },
    'consumer': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'yinShi_CS',
        'USER': 'yinShi_project',
        'PASSWORD': 'Con!082%Trib',
        'HOST': '127.0.0.1',
        'PORT': 3306,
    },
}

DATABASE_ROUTERS = ['Consumer_App.router.ConsumerAppRouter']

# Password validation
# https://docs.djangoproject.com/en/1.11/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/1.11/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Asia/Shanghai'

USE_I18N = True

USE_L10N = True

USE_TZ = False


AUTH_USER_MODEL = 'users.BusinessUser'

AUTHENTICATION_BACKENDS = (
    # 'django.contrib.auth.backends.ModelBackend',
    'users.auth.BusinessUserBackend',
)

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.11/howto/static-files/

STATIC_URL = '/static/'

STATIC_ROOT = os.path.join(BASE_DIR, 'static')

STATICFILES_DIRS = (
    ("picture", os.path.join(STATIC_ROOT, 'picture')),
)

OAUTH2_PROVIDER = {
    # this is the list of available scopes
    'SCOPES': {'read': 'Read scope', 'write': 'Write scope', 'groups': 'Access to your groups'},
    'ACCESS_TOKEN_EXPIRE_SECONDS': 60 * 60 * 20,
}

REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        # 'rest_framework.permissions.DjangoModelPermissionsOrAnonReadOnly',
        'rest_framework.permissions.IsAuthenticated',
    ],

    'DEFAULT_AUTHENTICATION_CLASSES': (
        'oauth2_provider.ext.rest_framework.OAuth2Authentication',

        # 'rest_framework.authentication.BasicAuthentication',
        # 'rest_framework.authentication.SessionAuthentication',
    ),

    # 'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.LimitOffsetPagination',
    # 'PAGE_SIZE': 100,
}

# pagination

PAGE_SIZE = 100

MAX_PAGE_SIZE = 500

# domain name
if ENVIRONMENT == 10:     # 开发环境
    DOMAIN_NAME = '121.42.249.43'
elif ENVIRONMENT == 20:   # 测试环境
    DOMAIN_NAME = '118.190.40.233'
elif ENVIRONMENT == 30:   # 生成环境
    DOMAIN_NAME = '118.190.166.150'
else:
    DOMAIN_NAME = '121.42.249.43'

# WEB URL FIX

WEB_URL_FIX = os.path.join('http://', DOMAIN_NAME)

# 图片目录
BUSINESS_PICTURE_ROOT = os.path.join(os.path.dirname(BASE_DIR), 'static', 'business', 'picture')
CONSUMER_PICTURE_ROOT = os.path.join(os.path.dirname(BASE_DIR), 'static', 'consume', 'picture')

# 静态文件根目录
BUSINESS_ROOT = os.path.join(os.path.dirname(BASE_DIR), 'static', 'business')

PICTURE_DIRS = {
    'consumer': {
        'head_picture': os.path.join(CONSUMER_PICTURE_ROOT, 'head_picture'),   # 用户头像图片目录
        'qrcode': os.path.join(CONSUMER_PICTURE_ROOT, 'qrcode'),               # 二维码图片目录
    },
    'business': {
        'dishes': os.path.join(BUSINESS_PICTURE_ROOT, 'dishes'),               # 菜品图片目录
        'head_picture': os.path.join(BUSINESS_PICTURE_ROOT, 'head_picture'),   # 用户头像图片目录
        'qrcode': os.path.join(BUSINESS_PICTURE_ROOT, 'qrcode'),               # 二维码图片目录
        'advert': os.path.join(BUSINESS_PICTURE_ROOT, 'advert'),               # 轮播广告图片目录
        'food_court': os.path.join(BUSINESS_PICTURE_ROOT, 'food_court'),       # 美食城图片目录
        'logo': os.path.join(BUSINESS_PICTURE_ROOT, 'logo'),                   # LOGO图片目录
        'app_package': os.path.join(BUSINESS_ROOT, 'app_package'),             # APP安装包目录
    }
}

# 缓存服务器配置
REDIS_SETTINGS = {
    'host': '127.0.0.1',
    'port': 6379,
    'db_set': {
        'business': 0,
        'consumer': 1,
    }
}

# 默认文件存储器
DEFAULT_FILE_STORAGE = 'horizon.storage.YSFileSystemStorage'


# 吟食支付二维码链接地址
if ENVIRONMENT == 10:      # 开发环境
    YINSHI_PAY_LINK = 'http://yinshi.weixin.city23.com/order/yinshi/?code=%s'
elif ENVIRONMENT == 20:    # 测试环境
    YINSHI_PAY_LINK = 'http://yinshi.weixin.city23.com/order/yinshi/?code=%s'
elif ENVIRONMENT == 30:    # 生产环境
    YINSHI_PAY_LINK = 'http://yinshin.net/order/yinshi/?code=%s'
else:
    YINSHI_PAY_LINK = 'http://yinshi.weixin.city23.com/order/yinshi/?code=%s'
