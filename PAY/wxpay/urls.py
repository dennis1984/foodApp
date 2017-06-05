# -*- coding:utf8 -*-
from django.conf.urls import url, include
from rest_framework.urlpatterns import format_suffix_patterns
from PAY.wxpay import views

# app_name = 'WXPay'

urlpatterns = [
    url(r'^native_callback/$', views.NativeCallback.as_view(), name='native_callback'),
]

urlpatterns = format_suffix_patterns(urlpatterns)


