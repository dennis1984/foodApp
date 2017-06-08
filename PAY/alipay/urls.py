# -*- coding:utf8 -*-
from django.conf.urls import url, include
from rest_framework.urlpatterns import format_suffix_patterns
from PAY.alipay import views

urlpatterns = [
    url(r'^precreate_callback/$', views.PreCreateCallback.as_view(), name='precreate_callback'),
]

urlpatterns = format_suffix_patterns(urlpatterns)


