# -*- coding:utf8 -*-
from django.conf.urls import url, include
from rest_framework.routers import DefaultRouter
from rest_framework.urlpatterns import format_suffix_patterns
from users import views as users_view

urlpatterns = [
    # url(r'^orders_detail/$', orders_view.OrdersDetail.as_view(), name='orders_detail'),
    # url(r'^create_orders/$', orders_view.OrdersAction.as_view(), name='create_orders'),

    url(r'user_action/$', users_view.UserAction.as_view()),
    # url(r'login/$', users_view)
]

urlpatterns = format_suffix_patterns(urlpatterns)


