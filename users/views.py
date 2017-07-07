# -*- coding: utf8 -*-
from rest_framework import viewsets
from rest_framework import generics
from rest_framework.response import Response
from rest_framework import status

from users.serializers import (UserSerializer,
                               UserInstanceSerializer,
                               UserDetailSerializer,
                               UserListSerializer,
                               IdentifyingCodeSerializer)
from users.permissions import IsAdminOrReadOnly, IsAuthenticated
from users.models import (BusinessUser,
                          make_token_expire,
                          IdentifyingCode)
from users.forms import (UsersInputForm,
                         ChangePasswordForm,
                         UserListForm,
                         SendIdentifyingCodeForm,
                         BusinessUserChangePasswordForm,
                         BusinessUserNoAuthResetPasswordForm)
from users.caches import BusinessUserCache
from horizon.views import APIView
from horizon import main


class IDYCodeAction(APIView):
    """
    发送手机验证码（未登录状态，适用于：忘记密码）
    """
    def is_valid_user(self, cld):
        instance = BusinessUserCache().get_user_by_username(cld['username'])
        if isinstance(instance, Exception):
            return False, Exception('The user does not existed.')
        return True, None

    def post(self, request, *args, **kwargs):
        """
        发送验证码
        """
        form = SendIdentifyingCodeForm(request.data)
        if not form.is_valid():
            return Response({'Detail': form.errors}, status=status.HTTP_400_BAD_REQUEST)

        cld = form.cleaned_data
        result = self.is_valid_user(cld)
        if not result[0]:
            return Response({'Detail': result[1].args}, status=status.HTTP_400_BAD_REQUEST)

        identifying_code = main.make_random_string_number(str_length=6)
        serializer = IdentifyingCodeSerializer(data={'phone': cld['username'],
                                                     'identifying_code': identifying_code})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        # 发送到短信平台
        main.send_identifying_code_to_phone({'code': identifying_code}, (cld['username'],))
        return Response(status=status.HTTP_200_OK)


class IDYCodeAuthAction(generics.GenericAPIView):
    """
    发送手机验证码（登录状态，适用于：重置密码）
    """
    permission_classes = (IsAuthenticated, )

    def post(self, request, *args, **kwargs):
        """
        发送验证码
        """
        identifying_code = main.make_random_string_number(str_length=6)
        serializer = IdentifyingCodeSerializer(data={'phone': request.user.phone,
                                                     'identifying_code': identifying_code})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        # 发送到短信平台
        main.send_identifying_code_to_phone({'code': identifying_code}, (request.user.phone,))
        return Response(status=status.HTTP_200_OK)


class UserAction(generics.GenericAPIView):
    """
    create user API
    """
    queryset = BusinessUser.objects.all()
    serializer_class = UserSerializer
    permission_classes = (IsAdminOrReadOnly, )

    def post(self, request, *args, **kwargs):
        """
         创建用户
        """
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
        """
        修改密码
        """
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


class BusinessUserAction(generics.GenericAPIView):
    permission_classes = (IsAuthenticated,)

    def is_valid_identifying_code(self, phone, identifying_code):
        _instance = IdentifyingCode.get_object_by_phone(phone)
        if not _instance:
            return False
        if _instance.identifying_code == identifying_code:
            return True
        return False

    def put(self, request, *args, **kwargs):
        """
        修改密码
        """
        form = BusinessUserChangePasswordForm(request.data)
        if not form.is_valid():
            return Response({'Detail': form.errors}, status=status.HTTP_400_BAD_REQUEST)

        cld = form.cleaned_data
        if not self.is_valid_identifying_code(request.user.phone, cld['identifying_code']):
            return Response({'Detail': 'Identifying code is incorrect or expired'},
                            status=status.HTTP_400_BAD_REQUEST)
        serializer = UserSerializer()
        try:
            serializer.update_password(request.user, cld)
        except Exception as e:
            return Response({'Detail': e.args}, status=status.HTTP_400_BAD_REQUEST)

        serializer_response = UserInstanceSerializer(request.user)
        return Response(serializer_response.data, status=status.HTTP_206_PARTIAL_CONTENT)


class BusinessUserNoAuthAction(APIView):
    def is_valid_identifying_code(self, phone, identifying_code):
        _instance = IdentifyingCode.get_object_by_phone(phone)
        if not _instance:
            return False
        if _instance.identifying_code == identifying_code:
            return True
        return False

    def get_user(self, user_name):
        return BusinessUserCache().get_user_by_username(user_name)

    def put(self, request, *args, **kwargs):
        """
        修改密码
        """
        form = BusinessUserNoAuthResetPasswordForm(request.data)
        if not form.is_valid():
            return Response({'Detail': form.errors}, status=status.HTTP_400_BAD_REQUEST)

        cld = form.cleaned_data
        if not self.is_valid_identifying_code(cld['username'], cld['identifying_code']):
            return Response({'Detail': 'Identifying code is incorrect or expired'},
                            status=status.HTTP_400_BAD_REQUEST)
        user = self.get_user(cld['username'])
        if isinstance(user, Exception):
            return Response({'Detail': user.args}, status=status.HTTP_400_BAD_REQUEST)
        serializer = UserSerializer()
        try:
            serializer.update_password(user, cld)
        except Exception as e:
            return Response({'Detail': e.args}, status=status.HTTP_400_BAD_REQUEST)

        serializer_response = UserInstanceSerializer(user)
        return Response(serializer_response.data, status=status.HTTP_206_PARTIAL_CONTENT)


class UserDetail(generics.GenericAPIView):
    queryset = BusinessUser.objects.all()
    serializer_class = UserDetailSerializer
    permission_classes = (IsAuthenticated, )

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


class AuthLogout(generics.GenericAPIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        """
        用户认证：登出
        """
        make_token_expire(request)
        return Response(status=status.HTTP_200_OK)


class UserViewSet(viewsets.ModelViewSet):
    """
    """
    queryset = BusinessUser.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer

