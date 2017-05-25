# -*- coding:utf8 -*-
from django.conf.urls import url, include
from rest_framework.routers import DefaultRouter
from rest_framework.urlpatterns import format_suffix_patterns
from orders import views as orders_view

urlpatterns = [
    url(r'^orders_detail/$', orders_view.OrdersDetail.as_view(), name='orders_detail'),
    url(r'^orders_action/$', orders_view.OrdersAction.as_view(), name='orders_action'),
    url(r'^orders_list/$', orders_view.OrdersList.as_view(), name='orders_list'),

    url(r'^sale_list/$', orders_view.SaleList.as_view(), name='sale_list'),
]

urlpatterns = format_suffix_patterns(urlpatterns)


