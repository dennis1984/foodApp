# -*- coding: utf8 -*-
from rest_framework.viewsets import ModelViewSet
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, permission_classes
from rest_framework import permissions

from rest_framework.renderers import JSONRenderer
from rest_framework.parsers import JSONParser
from rest_framework import status
from rest_framework.response import Response

from rest_framework import mixins
from rest_framework import generics
from django.utils.six import BytesIO
from orders.forms import OrdersInputForm, OrdersGetForm, OrdersUpdateForm,\
    OrdersListForm
from orders.models import Orders
from orders.serializers import OrdersSerializer, OrdersListSerializer
from orders.permissoins import IsOwnerOrReadOnly


class OrdersAction(generics.GenericAPIView):
    queryset = Orders.objects.all()
    serializer_class = OrdersSerializer

    def post(self, request, *args, **kwargs):
        """
        :param request: 
        :param args: 
        :param kwargs: {'dishes_ids': [{'dishes_id': '',
                                       'count': '',
                                       }, ...
                                       ],
                        }
        :return: 
        """
        form = OrdersInputForm(request.data)
        if not form.is_valid():
            return Response(form.errors, status=status.HTTP_400_BAD_REQUEST)

        cld = form.cleaned_data
        stream = BytesIO(cld['dishes_ids'])
        dishes_ids = JSONParser().parse(stream)

        object_data = Orders.make_orders_by_dishes_ids(request, dishes_ids=dishes_ids)
        if isinstance(object_data, Exception):
            return Response({'Error': object_data.args}, status=status.HTTP_400_BAD_REQUEST)

        serializer = OrdersSerializer(data=object_data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, *args, **kwargs):
        """
        更新订单状态
        :param request:
        :param args:
        :param kwargs: 'order_id': 订单ID
                       'payment_status': 订单支付状态
        :return: Orders instance
        """
        form = OrdersUpdateForm(request.data)
        if not form.is_valid():
            return Response(form.errors, status=status.HTTP_400_BAD_REQUEST)

        cld = form.cleaned_data
        obj = Orders.get_object(**{'order_id': cld['order_id']})
        if isinstance(obj, Exception):
            return Response({'Error': obj.args}, status=status.HTTP_400_BAD_REQUEST)

        serializer = OrdersSerializer(obj)
        try:
            serializer.update_payment_status(obj, cld)
        except Exception as e:
            return Response({'Error': e.args}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.data, status=status.HTTP_206_PARTIAL_CONTENT)


class OrdersDetail(generics.GenericAPIView):
    queryset = Orders.objects.all()
    serializer_class = OrdersSerializer

    def get_object(self, *args, **kwargs):
        try:
            return Orders.objects.get(**kwargs)
        except Orders.DoesNotExist:
            raise status.HTTP_404_NOT_FOUND

    def post(self, request, *args, **kwargs):
        """
        :param request:
        :param args:
        :param kwargs: {'orders_id': '',
                        }
        :return:
        """
        form = OrdersGetForm(request.data)
        if not form.is_valid():
            return Response(form.errors, status=status.HTTP_400_BAD_REQUEST)

        cld = form.cleaned_data
        for key in cld.keys():
            if not cld[key]:
                cld.pop(key)

        object_data = Orders.get_object_by_orders_id(**cld)
        if isinstance(object_data, Exception):
            return Response({'Error': object_data.args}, status=status.HTTP_400_BAD_REQUEST)
        serializer = OrdersSerializer(object_data)
        return Response(serializer.data, status=status.HTTP_200_OK)


class OrdersList(generics.GenericAPIView):
    queryset = Orders.objects.all()
    serializer_class = OrdersSerializer
    permissions = (IsOwnerOrReadOnly,)

    def get_objects_list(self, request, **kwargs):
        kwargs['user_id'] = request.user.id
        return Orders.get_objects_list(**kwargs)

    def post(self, request, *args, **kwargs):
        """
        :param request:
        :param args:
        :param kwargs: {'orders_id': '',
                        }
        :return:
        """
        form = OrdersListForm(request.data)
        if not form.is_valid():
            return Response(form.errors, status=status.HTTP_400_BAD_REQUEST)

        cld = form.cleaned_data
        for key in cld.keys():
            if not cld[key]:
                cld.pop(key)

        object_data = self.get_objects_list(request, **cld)
        if isinstance(object_data, Exception):
            return Response({'Error': object_data.args}, status=status.HTTP_400_BAD_REQUEST)

        serializer = OrdersListSerializer(object_data)
        results = serializer.list_data(**cld)
        if isinstance(results, Exception):
            return Response({'Error': results.args}, status=status.HTTP_400_BAD_REQUEST)
        return Response(results, status=status.HTTP_200_OK)

