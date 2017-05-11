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
from django.contrib import admin
from django.contrib.auth.models import User
from rest_framework import routers, serializers, viewsets

import orders


# Serializers定义了API的表现形式
class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ('url', 'username', 'email', 'is_staff')


# ViewSets定义了视图view的行为
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer


# Routers提供了一种简单途径，自动配置了URL
router = routers.DefaultRouter()
router.register(r'users', UserViewSet)


urlpatterns = [
    url(r'^admin/', admin.site.urls),

    url(r'^', include(router.urls)),
    url(r'^api-auth', include('rest_framework.urls', namespace='rest_framework')),

    url(r'^orders/', include('orders.urls')),
]
