# -*- coding:utf8 -*-

from django.conf.urls import url, include
from rest_framework.routers import DefaultRouter
from rest_framework.urlpatterns import format_suffix_patterns
from dishes import views as dishes_view

urlpatterns = [
    url(r'^dishes_detail/(?P<pk>[0-9]+)/$', dishes_view.DishesList.as_view()),
    # url(r'save_orders/', orders_view.save_order, name='save_order'),
]

urlpatterns = format_suffix_patterns(urlpatterns)


