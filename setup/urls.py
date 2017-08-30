# -*- coding:utf8 -*-
from django.conf.urls import url, include
from rest_framework.routers import DefaultRouter
from rest_framework.urlpatterns import format_suffix_patterns
from setup import views

urlpatterns = [
    url(r'^app_version_detail/$', views.AppVersionDetail.as_view()),
]

urlpatterns = format_suffix_patterns(urlpatterns)


