# -*- coding:utf8 -*-
from django.conf.urls import url, include
from rest_framework.routers import DefaultRouter
from rest_framework.urlpatterns import format_suffix_patterns
from dishes import views as dishes_view

urlpatterns = [
    url(r'^dishes_action/$', dishes_view.DishesAction.as_view()),
    url(r'^dishes_detail/$', dishes_view.DishesDetail.as_view()),
    url(r'^dishes_list/$', dishes_view.DishesList.as_view()),

    url(r'^dishes_classify_action/$', dishes_view.DishesClassifyAction.as_view()),
    url(r'^dishes_classify_list/$', dishes_view.DishesClassifyList.as_view()),

    url(r'^food_court_action/$', dishes_view.FoodCourtAction.as_view()),
    url(r'^food_court_detail/$', dishes_view.FoodCourtDetail.as_view()),
    url(r'^food_court_list/$', dishes_view.FoodCourtList.as_view()),

    # 测试临时用
    # url(r'^dishes_detail/(?P<pk>[0-9]+)/$', dishes_view.DishesDetail.as_view()),
]

urlpatterns = format_suffix_patterns(urlpatterns)


