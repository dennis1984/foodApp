# -*- coding: utf8 -*-
from rest_framework import status
from rest_framework.response import Response
from rest_framework import generics
from rest_framework import permissions

from dishes.models import (Dishes,
                           FoodCourt,
                           DISHES_SIZE_DICT,
                           DishesClassify)
from dishes.serializers import (DishesSerializer,
                                FoodCourtSerializer,
                                DishesListSerializer,
                                FoodCourtListSerializer,
                                DishesClassifySerializer,
                                DishesClassifyListSerializer)
from dishes.forms import (DishesGetForm,
                          DishesInputForm,
                          FoodCourtListForm,
                          FoodCourtGetForm,
                          DishesUpdateForm,
                          DishesDeleteForm,
                          DishesListForm,
                          DishesClassifyInputForm,
                          DishesClassifyUpdateForm,
                          DishesClassifyDeleteForm,
                          DishesClassifyListForm)
from dishes.permissions import IsOwnerOrReadOnly
from users.permissions import IsAdminOrReadOnly
from dishes.caches import DishesCache


class DishesAction(generics.GenericAPIView):
    permission_classes = (IsOwnerOrReadOnly, )

    def get_dishes_classify_object(self, request, dishes_classify_id):
        kwargs = {'user_id': request.user.id,
                  'id': dishes_classify_id}
        return DishesClassify.get_object(**kwargs)

    def is_valid_request_data(self, request, **cld):
        size = cld.get('size', DISHES_SIZE_DICT['default'])
        if size not in DISHES_SIZE_DICT.values():
            return False, 'Size fields is incorrect'
        if size == DISHES_SIZE_DICT['custom']:
            if not cld.get('size_detail'):
                return False, 'When size is 20, size detail is required'
        if 'classify' in cld:
            dishes_classify_ins = self.get_dishes_classify_object(request, cld['classify'])
            if isinstance(dishes_classify_ins, Exception):
                return False, dishes_classify_ins.args
        return True, None

    def get_dishes_object(self, request, cld):
        kwargs = {'user_id': request.user.id,
                  'pk': cld['pk']}
        return Dishes.get_object(**kwargs)

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
        form = DishesInputForm(request.data)
        if not form.is_valid():
            return Response({'Detail': form.errors}, status=status.HTTP_400_BAD_REQUEST)

        cld = form.cleaned_data
        is_valid, error_message = self.is_valid_request_data(request, **cld)
        if not is_valid:
            return Response({'Detail': error_message}, status=status.HTTP_400_BAD_REQUEST)

        serializer = DishesSerializer(data=cld, request=request)
        if serializer.is_valid():
            result = serializer.save(request)
            if isinstance(result, Exception):
                return Response({'Detail': result.args}, status=status.HTTP_400_BAD_REQUEST)
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
        is_valid, error_message = self.is_valid_request_data(request, **cld)
        if not is_valid:
            return Response({'Detail': error_message}, status=status.HTTP_400_BAD_REQUEST)
        obj = self.get_dishes_object(request, cld)
        if isinstance(obj, Exception):
            return Response({'Detail': obj.args}, status=status.HTTP_400_BAD_REQUEST)
        serializer = DishesSerializer(obj)
        try:
            serializer.update_dishes(request, obj, cld)
        except Exception as e:
            return Response({'Detail': e.args}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.data, status=status.HTTP_206_PARTIAL_CONTENT)

    def delete(self, request, *args, **kwargs):
        """
        删除菜品
        :return: Dishes object
        """
        form = DishesDeleteForm(request.data)
        if not form.is_valid():
            return Response(form.errors, status=status.HTTP_400_BAD_REQUEST)

        obj = self.get_dishes_object(request, form.cleaned_data)
        if isinstance(obj, Exception):
            return Response({'Detail': obj.args}, status=status.HTTP_400_BAD_REQUEST)
        serializer = DishesSerializer(obj)
        try:
            serializer.delete(request, obj)
        except Exception as e:
            return Response({'Detail': e.args}, status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.data, status=status.HTTP_204_NO_CONTENT)


class DishesDetail(generics.GenericAPIView):
    permission_classes = (IsOwnerOrReadOnly,)

    def get_dishes_detail(self, **kwargs):
        return Dishes.get_detail(**kwargs)

    def post(self, request, *args, **kwargs):
        """
        """
        form = DishesGetForm(request.data)
        if not form.is_valid():
            return Response(form.errors, status=status.HTTP_400_BAD_REQUEST)

        cld = form.cleaned_data
        if not cld:
            return Response(cld, status=status.HTTP_200_OK)

        detail = self.get_dishes_detail(**cld)
        serializer = DishesSerializer(data=detail)
        if not serializer.is_valid():
            return Response({'Detail': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.data, status=status.HTTP_200_OK)


class DishesList(generics.GenericAPIView):
    permission_classes = (IsOwnerOrReadOnly, )

    def get_object_list(self, request, **kwargs):
        if kwargs.get('gateway') == 'edit_page':
            return Dishes.filter_details(request, **kwargs)
        else:
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
        details = self.get_object_list(request, **cld)
        if isinstance(details, Exception):
            return Response({'detail': details.args}, status=status.HTTP_400_BAD_REQUEST)

        serializer = DishesListSerializer(data=details)
        if not serializer.is_valid():
            return Response({'Detail': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        list_data = serializer.list_data(**cld)
        if isinstance(list_data, Exception):
            return Response({'Detail': list_data.args}, status=status.HTTP_400_BAD_REQUEST)
        return Response(list_data, status=status.HTTP_200_OK)


class FoodCourtAction(generics.GenericAPIView):
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
        serializer = FoodCourtListSerializer(filter_list)
        results = serializer.list_data(**cld)
        if isinstance(results, Exception):
            return Response({'Error': results.args}, status=status.HTTP_400_BAD_REQUEST)
        return Response(results, status=status.HTTP_200_OK)


class FoodCourtDetail(generics.GenericAPIView):
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


class DishesClassifyAction(generics.GenericAPIView):
    """
    创建菜品类别
    """
    permission_classes = (IsOwnerOrReadOnly, )

    def get_dishes_classify_object(self, request, dishes_classify_id):
        kwargs = {'user_id': request.user.id,
                  'id': dishes_classify_id}
        return DishesClassify.get_object(**kwargs)

    def post(self, request, *args, **kwargs):
        """
        创建菜品类别
        """
        form = DishesClassifyInputForm(request.data)
        if not form.is_valid():
            return Response({'Detail': form.errors}, status=status.HTTP_400_BAD_REQUEST)

        cld = form.cleaned_data
        serializer = DishesClassifySerializer(data=cld, request=request)
        if not serializer.is_valid():
            return Response({'Detail': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        try:
            serializer.save()
        except Exception as e:
            return Response({'Detail': e.args}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def put(self, request, *args, **kwargs):
        """
        更改菜品类别
        """
        form = DishesClassifyUpdateForm(request.data)
        if not form.is_valid():
            return Response(form.errors, status=status.HTTP_400_BAD_REQUEST)

        cld = form.cleaned_data
        ins = self.get_dishes_classify_object(request, cld['id'])
        if isinstance(ins, Exception):
            return Response({'Detail': ins.args}, status=status.HTTP_400_BAD_REQUEST)
        serializer = DishesClassifySerializer(ins)
        try:
            serializer.update(ins, cld)
        except Exception as e:
            return Response({'Detail': e.args}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.data, status=status.HTTP_206_PARTIAL_CONTENT)

    def delete(self, request, *args, **kwargs):
        """
        删除菜品
        """
        form = DishesClassifyDeleteForm(request.data)
        if not form.is_valid():
            return Response(form.errors, status=status.HTTP_400_BAD_REQUEST)

        cld = form.cleaned_data
        ins = self.get_dishes_classify_object(request, cld['id'])
        if isinstance(ins, Exception):
            return Response({'Detail': ins.args}, status=status.HTTP_400_BAD_REQUEST)
        serializer = DishesClassifySerializer(ins)
        try:
            serializer.delete(ins)
        except Exception as e:
            return Response({'Detail': e.args}, status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.data, status=status.HTTP_204_NO_CONTENT)


class DishesClassifyList(generics.GenericAPIView):
    permission_classes = (IsOwnerOrReadOnly, )

    def get_object_list(self, request):
        kwargs = {'user_id': request.user.id}
        return DishesClassify.filter_objects(**kwargs)

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
        form = DishesClassifyListForm(request.data)
        if not form.is_valid():
            return Response(form.errors, status=status.HTTP_400_BAD_REQUEST)

        cld = form.cleaned_data
        instances = self.get_object_list(request)
        if isinstance(instances, Exception):
            return Response({'Detail': instances.args}, status=status.HTTP_400_BAD_REQUEST)

        serializer = DishesClassifyListSerializer(instances)
        data_list = serializer.list_data(**cld)
        if isinstance(data_list, Exception):
            return Response({'Detail': data_list.args}, status=status.HTTP_400_BAD_REQUEST)
        return Response(data_list, status=status.HTTP_200_OK)


