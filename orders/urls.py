# -*- coding:utf8 -*-
from django.conf.urls import url, include
from rest_framework.routers import DefaultRouter
from rest_framework.urlpatterns import format_suffix_patterns
# from orders.views import OrdersViewSet
from orders import views as orders_view

# router = DefaultRouter()  # 定义 router
# router.register('orders', OrdersViewSet)  # 注册 viewset

urlpatterns = [
    # url(r'^', OrdersViewSet.as_view()),  # 在 urlpatterns 里包含 router
    # url(r'orders_list/', orders_view.OrdersList.as_view(), name='orders_list'),

    url(r'^orders_detail/$', orders_view.OrdersDetail.as_view(), name='orders_detail'),
    url(r'^create_orders/$', orders_view.OrdersAction.as_view(), name='create_orders'),
]

urlpatterns = format_suffix_patterns(urlpatterns)


