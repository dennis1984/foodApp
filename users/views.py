# -*- coding: utf8 -*-
from django.contrib.auth.models import User, Group
from rest_framework import viewsets
from rest_framework import generics
from rest_framework.response import Response
from rest_framework import status

from users.serializers import UserSerializer, UserInstanceSerializer, \
    UserDetailSerializer, UserListSerializer
from users.permissions import IsAdminOrReadOnly
from users.models import BusinessUser, make_token_expire
from users.forms import UsersInputForm, ChangePasswordForm, UserListForm


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

        serializer = UserInstanceSerializer(user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

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

        serializer_response = UserInstanceSerializer(obj)
        return Response(serializer_response.data, status=status.HTTP_206_PARTIAL_CONTENT)


class UserDetail(generics.GenericAPIView):
    queryset = BusinessUser.objects.all()
    serializer_class = UserDetailSerializer
    # permission_classes = (IsAdminOrReadOnly, )

    def post(self, request, *args, **kwargs):
        user = BusinessUser.get_user_detail(request)
        if isinstance(user, Exception):
            return Response({'Error': user.args}, status=status.HTTP_400_BAD_REQUEST)

        serializer = UserDetailSerializer(data=user)
        if serializer.is_valid():
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserList(generics.GenericAPIView):
    queryset = BusinessUser.objects.all()
    serializer_class = UserDetailSerializer
    permission_classes = (IsAdminOrReadOnly, )

    def get_objects_list(self, request, **kwargs):
        return BusinessUser.get_objects_list(request, **kwargs)

    def post(self, request, *args, **kwargs):
        form = UserListForm(request.data)
        if not form.is_valid():
            return Response(form.errors, status=status.HTTP_400_BAD_REQUEST)

        cld = form.cleaned_data
        _objects = self.get_objects_list(request, **kwargs)
        if isinstance(_objects, Exception):
            return Response({'detail': _objects.args}, status=status.HTTP_400_BAD_REQUEST)

        serializer = UserListSerializer(data=_objects)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        results = serializer.list_data(**cld)
        if isinstance(results, Exception):
            return Response({'Error': results.args}, status=status.HTTP_400_BAD_REQUEST)
        return Response(results, status=status.HTTP_200_OK)


# class AuthLogin(generics.GenericAPIView):
#     """
#     用户认证：登录
#     """
#     def post(self, request, *args, **kwargs):
#         pass
#
#
class AuthLogout(generics.GenericAPIView):
    """
    用户认证：登出
    """
    def post(self, request, *args, **kwargs):
        make_token_expire(request)
        return Response(status=status.HTTP_200_OK)


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

