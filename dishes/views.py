# -*- coding: utf8 -*-
from rest_framework.renderers import JSONRenderer
from rest_framework.parsers import JSONParser
from rest_framework import status
from rest_framework.response import Response
from rest_framework import mixins
from rest_framework import generics
from rest_framework import permissions

from dishes.models import Dishes, FoodCourt
from dishes.serializers import (DishesSerializer,
                                FoodCourtSerializer,
                                DishesListSerializer,
                                FoodCourtListSerializer)
from dishes.forms import (DishesGetForm,
                          FoodCourtListForm,
                          FoodCourtGetForm,
                          DishesUpdateForm,
                          DishesDeleteForm,
                          DishesListForm)
from dishes.permissions import IsOwnerOrReadOnly
from users.permissions import IsAdminOrReadOnly
from dishes.caches import DishesCache


class DishesAction(mixins.CreateModelMixin, generics.GenericAPIView):
    queryset = Dishes.objects.all()
    serializer_class = DishesSerializer
    permission_classes = (IsOwnerOrReadOnly, )

    # def make_cache_expired(self, request, *args, **kwargs):
    #     DishesCache().delete_dishes_list(request)

    def post(self, request, *args, **kwargs):
        """
        :param request: 
        :param args: 
        :param kwargs: {'title': '', 
                        'subtitle': '',
                        'description': '',
                        'price': '',
                        'size': Integer,
                        'image': Image,
                        }
        :return: Dishes object
        """
        serializer = DishesSerializer(_request=request)
        if serializer.is_valid():
            serializer.save(request)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, *args, **kwargs):
        """
        更改菜品信息
        :param request:
        :param args:
        :param kwargs: {'pk': Integer,
                        'subtitle': '',
                        'description': '',
                        'price': '',
                        'size': Integer,
                        'image': Image,
                        'is_recommend': Integer,
                        }
        :return: Dishes object
        """
        form = DishesUpdateForm(request.data)
        if not form.is_valid():
            return Response(form.errors, status=status.HTTP_400_BAD_REQUEST)

        cld = form.cleaned_data
        obj = Dishes.get_object(**{'pk': cld['pk']})
        cld.pop('pk')
        if isinstance(obj, Exception):
            return Response({'Error': obj.args}, status=status.HTTP_400_BAD_REQUEST)
        serializer = DishesSerializer(obj)
        try:
            serializer.update_dishes(request, obj, cld)
        except Exception as e:
            return Response({'Error': e.args}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.data, status=status.HTTP_206_PARTIAL_CONTENT)

    def delete(self, request, *args, **kwargs):
        """
        删除菜品
        :param request:
        :param args:
        :param kwargs: pk
        :return: Dishes object
        """
        form = DishesDeleteForm(request.data)
        if not form.is_valid():
            return Response(form.errors, status=status.HTTP_400_BAD_REQUEST)

        obj = Dishes.get_object(**{'pk': form.cleaned_data['pk']})
        if isinstance(obj, Exception):
            return Response({'Error': obj.args}, status=status.HTTP_400_BAD_REQUEST)
        serializer = DishesSerializer(obj)
        try:
            serializer.delete(request, obj)
        except Exception as e:
            return Response({'Error': e.args}, status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.data, status=status.HTTP_204_NO_CONTENT)


class DishesDetail(mixins.RetrieveModelMixin, generics.GenericAPIView):
    queryset = Dishes.objects.all()
    serializer_class = DishesSerializer
    permission_classes = (IsOwnerOrReadOnly,)

    def get_object(self, *args, **kwargs):
        try:
            return Dishes.objects.get(**kwargs)
        except Dishes.DoesNotExist:
            raise status.HTTP_404_NOT_FOUND

    def post(self, request, *args, **kwargs):
        """
        """
        form = DishesGetForm(request.data)
        if not form.is_valid():
            return Response(form.errors, status=status.HTTP_400_BAD_REQUEST)

        cld = form.cleaned_data
        if not cld:
            return Response(cld, status=status.HTTP_200_OK)

        object_data = self.get_object(**cld)
        serializer = DishesSerializer(object_data)
        return Response(serializer.data, status=status.HTTP_200_OK)

    # def get(self, request, pk, *args, **kwargs):
    #     """
    #     测试用
    #     """
    #     object_data = self.get_object(**{'pk': pk})
    #     serializer = DishesResponseSerializer(object_data)
    #     return Response(serializer.data, status=status.HTTP_200_OK)


class DishesList(generics.GenericAPIView):
    queryset = Dishes.objects.all()
    serializer_class = DishesSerializer
    permission_classes = (IsOwnerOrReadOnly, )

    def get_object_list(self, request, **kwargs):
        dishes_cache = DishesCache()
        return dishes_cache.get_dishes_list(request, **kwargs)

    def post(self, request, *args, **kwargs):
        """
        带分页功能
        返回数据格式为：{'count': 当前返回的数据量,
                       'all_count': 总数据量,
                       'has_next': 是否有下一页,
                       'data': [{
                                 Dishes model数据
                                },...]
                       }
        """
        form = DishesListForm(request.data)
        if not form.is_valid():
            return Response(form.errors, status=status.HTTP_400_BAD_REQUEST)

        cld = form.cleaned_data
        object_data = self.get_object_list(request, **cld)
        if isinstance(object_data, Exception):
            return Response({'detail': object_data.args}, status=status.HTTP_400_BAD_REQUEST)

        serializer = DishesListSerializer(object_data)
        # serializer = DishesSerializer(object_data, many=True)
        results = serializer.list_data(**cld)
        if isinstance(results, Exception):
            return Response({'Error': results.args}, status=status.HTTP_400_BAD_REQUEST)
        return Response(results, status=status.HTTP_200_OK)


class FoodCourtAction(generics.GenericAPIView):
    queryset = FoodCourt.objects.all()
    serializer_class = FoodCourtSerializer
    permission_classes = (IsAdminOrReadOnly, )

    def post(self, request, *args, **kwargs):
        """
        :param request:
        :param args:
        :param kwargs: {'name': '',
                        'city': '',
                        'district': '',
                        'mall': '',
                        }
        :return:
        """
        serializer = FoodCourtSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class FoodCourtList(generics.GenericAPIView):
    queryset = FoodCourt.objects.all()
    serializer_class = FoodCourtSerializer
    permission_classes = (IsAdminOrReadOnly, )

    def get_object_list(self, **kwargs):
        try:
            return FoodCourt.get_object_list(**kwargs)
        except Exception as e:
            raise e

    def post(self, request, *args, **kwargs):
        """
        带分页功能
        返回数据格式为：{'count': 当前返回的数据量,
                       'all_count': 总数据量,
                       'has_next': 是否有下一页,
                       'data': [{
                                 FoodCourt model数据
                                },...]
                       }
        """
        form = FoodCourtListForm(request.data)
        if not form.is_valid():
            return Response(form.errors, status=status.HTTP_400_BAD_REQUEST)

        cld = form.cleaned_data
        try:
            filter_list = self.get_object_list(**cld)
        except Exception as e:
            return Response({'Error': e.args}, status=status.HTTP_400_BAD_REQUEST)
        # serializer = FoodCourtSerializer(filter_list, many=True)
        serializer = FoodCourtListSerializer(filter_list)
        results = serializer.list_data(**cld)
        if isinstance(results, Exception):
            return Response({'Error': results.args}, status=status.HTTP_400_BAD_REQUEST)
        return Response(results, status=status.HTTP_200_OK)


class FoodCourtDetail(generics.GenericAPIView):
    queryset = FoodCourt.objects.all()
    serializer_class = FoodCourtSerializer
    permission_classes = (IsAdminOrReadOnly, )

    def get_object_detail(self, **kwargs):
        try:
            return FoodCourt.objects.get(**kwargs)
        except Exception as e:
            raise e

    def post(self, request, *args, **kwargs):
        """
        获取美食城的详情
        """
        form = FoodCourtGetForm(request.data)
        if not form.is_valid():
            return Response(form.errors, status=status.HTTP_400_BAD_REQUEST)

        cld = form.cleaned_data
        try:
            obj = self.get_object_detail(**cld)
        except Exception as e:
            return Response({'Error': e.args}, status=status.HTTP_400_BAD_REQUEST)
        serializer = FoodCourtSerializer(obj)
        return Response(serializer.data, status=status.HTTP_200_OK)

