# -*- coding: utf8 -*-
from django.contrib.auth.models import User, Group
from rest_framework import viewsets
from rest_framework import generics
from rest_framework.response import Response
from rest_framework import status

from users.serializers import UserSerializer, GroupSerializer, \
    UserResponseSerializer
from users.permissions import IsAdminOrReadOnly
from users.models import BusinessUser
from users.forms import UsersInputForm, ChangePasswordForm


class UserAction(generics.GenericAPIView):
    """
    create user API
    """
    queryset = BusinessUser.objects.all()
    serializer_class = UserSerializer
    permission_classes = (IsAdminOrReadOnly, )

    def post(self, request, *args, **kwargs):
        form = UsersInputForm(request.data)
        if not form.is_valid():
            return Response(form.errors, status=status.HTTP_400_BAD_REQUEST)

        cld = form.cleaned_data
        try:
            user = BusinessUser.objects.create_user(**cld)
        except Exception as e:
            return Response({'Error': e.args}, status=status.HTTP_400_BAD_REQUEST)

        serializer = UserResponseSerializer(user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

        # serializer = UserSerializer(data=cld)
        # if serializer.is_valid():
        #     serializer.save()
        #     return Response(serializer.data, status=status.HTTP_201_CREATED)
        # return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, *args, **kwargs):
        form = ChangePasswordForm(request.data)
        if not form.is_valid():
            return Response(form.errors, status=status.HTTP_400_BAD_REQUEST)

        obj = BusinessUser.get_object(**{'pk': request.user.id})
        serializer = UserSerializer(obj)
        try:
            serializer.update_password(obj, form.cleaned_data)
        except Exception as e:
            return Response({'Error': e.args}, status=status.HTTP_400_BAD_REQUEST)

        serializer_response = UserResponseSerializer(obj)
        return Response(serializer_response.data, status=status.HTTP_206_PARTIAL_CONTENT)


class UserDetail(generics.GenericAPIView):
    queryset = BusinessUser.objects.all()
    serializer_class = UserResponseSerializer
    # permission_classes = (IsAdminOrReadOnly, )

    def post(self, request, *args, **kwargs):
        user = BusinessUser.get_user_detail(request)
        if isinstance(user, Exception):
            return Response({'Error': user.args}, status=status.HTTP_400_BAD_REQUEST)

        serializer = UserResponseSerializer(data=user)
        if serializer.is_valid():
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AuthLogin(generics.GenericAPIView):
    """
    用户认证：登录
    """
    def post(self, request, *args, **kwargs):
        pass


class AuthLogout(generics.GenericAPIView):
    """
    用户认证：登出
    """
    def post(self, request, *args, **kwargs):
        pass


class UserViewSet(viewsets.ModelViewSet):
    """
    """
    queryset = BusinessUser.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer

#
# class GroupViewSet(viewsets.ModelViewSet):
#     """
#     """
#     queryset = Group.objects.all()
#     serializer_class = GroupSerializer
#
#
# class UserList(generics.ListAPIView):
#     queryset = BusinessUser.objects.all()
#     serializer_class = UserSerializer
#
#
# class UserDetail(generics.RetrieveAPIView):
#     queryset = BusinessUser.objects.all()
#     serializer_class = UserSerializer

