# -*- coding:utf8 -*-

from django.conf.urls import url, include
from rest_framework.routers import DefaultRouter
from rest_framework.urlpatterns import format_suffix_patterns
from dishes import views as dishes_view

urlpatterns = [
    url(r'^dishes_action/$', dishes_view.DishesAction.as_view()),
    url(r'^dishes_detail/$', dishes_view.DishesDetail.as_view()),
]

urlpatterns = format_suffix_patterns(urlpatterns)


