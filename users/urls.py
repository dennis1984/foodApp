# -*- coding:utf8 -*-
from django.conf.urls import url, include
from rest_framework.routers import DefaultRouter
from rest_framework.urlpatterns import format_suffix_patterns
from users import views

urlpatterns = (
    url(r'^send_reset_identifying_code/$', views.IDYCodeAuthAction.as_view()),
    url(r'^send_forget_identifying_code/$', views.IDYCodeAction.as_view()),

    url(r'^business_user_action/$', views.BusinessUserAction.as_view()),
    url(r'^business_user_no_auth_action/$', views.BusinessUserNoAuthAction.as_view()),
    url(r'^user_action/$', views.UserAction.as_view()),
    url(r'^user_detail/$', views.UserDetail.as_view()),
    url(r'^user_list/$', views.UserList.as_view()),

    url(r'^client_detail_action/$', views.ClientDetailAction.as_view()),
    url(r'^client_detail_show/$', views.ClientDetailShow.as_view()),

    url(r'^logout/$', views.AuthLogout.as_view()),
)

urlpatterns = format_suffix_patterns(urlpatterns)


