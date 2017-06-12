#-*- coding:utf8 -*-
"""foodApp URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, include
from rest_framework import routers

# from users import views
# router = routers.DefaultRouter()
# router.register(r'users', views.UserViewSet)

urlpatterns = [
    # url(r'^api-auth', include('rest_framework.urls', namespace='rest_framework')),
    # url(r'^api-token-auth/', authtoken_views.obtain_auth_token),
    url(r'^o/', include('oauth2_provider.urls', namespace='oauth2_provider')),

    url(r'^orders/', include('orders.urls')),
    url(r'^dishes/', include('dishes.urls', namespace='dishes_app')),
    url(r'^auth/', include('users.urls')),

    url(r'^wxpay/', include('PAY.wxpay.urls', namespace='wxpay')),
    url(r'^alipay/', include('PAY.alipay.urls', namespace='alipay')),
]
