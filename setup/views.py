# -*- coding: utf8 -*-
from rest_framework import status
from rest_framework.response import Response
from rest_framework import generics

from setup.models import AppVersion
from setup.serializers import (AppVersionSerializer)
from setup.permissions import IsOwnerOrReadOnly


class AppVersionDetail(generics.GenericAPIView):
    permission_classes = (IsOwnerOrReadOnly, )

    def get_last_object(self):
        return AppVersion.get_last_version()

    def post(self, request, *args, **kwargs):
        """
        获取最新版本号
        """
        instance = self.get_last_object()
        if isinstance(instance, Exception):
            return Response({}, status=status.HTTP_400_BAD_REQUEST)

        serializer = AppVersionSerializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)
