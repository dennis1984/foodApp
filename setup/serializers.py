# -*- coding:utf8 -*-
from rest_framework import serializers
from django.utils.timezone import now
from django.conf import settings

from horizon.serializers import (BaseModelSerializer,
                                 BaseListSerializer,
                                 BaseSerializer)
from setup.models import AppVersion


import datetime
import json


class AppVersionSerializer(BaseModelSerializer):
    def __init__(self, instance=None, data=None, request=None, **kwargs):
        if data and request:
            super(AppVersionSerializer, self).__init__(data=data, **kwargs)
        else:
            super(AppVersionSerializer, self).__init__(instance, **kwargs)

    class Meta:
        model = AppVersion
        fields = '__all__'
