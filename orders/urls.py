# -*- coding:utf8 -*-
from django.conf.urls import url, include
from rest_framework.routers import DefaultRouter
from rest_framework.urlpatterns import format_suffix_patterns
from orders import views as orders_view

urlpatterns = [
    url(r'^orders_detail/$', orders_view.OrdersDetail.as_view(), name='orders_detail'),
    url(r'^orders_action/$', orders_view.OrdersAction.as_view(), name='orders_action'),
    url(r'^orders_list/$', orders_view.OrdersList.as_view(), name='orders_list'),

    url(r'^verify_orders_list/$', orders_view.VerifyOrdersList.as_view()),
    url(r'^verify_orders_action/$', orders_view.VerifyOrdersAction.as_view()),
    url(r'^verify_orders_detail/$', orders_view.VerifyOrdersDetail.as_view()),

    url(r'^sale_orders_list/$', orders_view.SaleOrdersList.as_view(), name='sale_orders_list'),
    url(r'^sale_dishes_list/$', orders_view.SaleDishesList.as_view(), name='sale_dishes_list'),
]

urlpatterns = format_suffix_patterns(urlpatterns)


