# -*- coding: utf8 -*-
from rest_framework.parsers import JSONParser
from rest_framework import status
from rest_framework.response import Response

from rest_framework import generics
from django.utils.six import BytesIO
from orders.forms import OrdersInputForm, OrdersGetForm, OrdersUpdateForm,\
    OrdersListForm, SaleListForm
from orders.models import Orders, get_sale_list
from orders.serializers import OrdersSerializer, OrdersListSerializer, \
    SaleListSerializer, DishesIdsDetailSerializer
from orders.permissoins import IsOwnerOrReadOnly

from orders.pays import WXPay


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
                       'payment_mode': 订单支付方式
        :return: Orders instance
        """
        form = OrdersUpdateForm(request.data)
        if not form.is_valid():
            return Response(form.errors, status=status.HTTP_400_BAD_REQUEST)

        cld = form.cleaned_data
        obj = Orders.get_object(**{'orders_id': cld['orders_id']})
        if isinstance(obj, Exception):
            return Response({'Error': obj.args}, status=status.HTTP_400_BAD_REQUEST)

        serializer = OrdersSerializer(obj)
        try:
            serializer.update_orders_status(obj, cld)
        except Exception as e:
            return Response({'Error': e.args}, status=status.HTTP_400_BAD_REQUEST)

        payment_mode = cld['payment_mode']
        if cld['payment_status'] or payment_mode == 1:
            # 更新支付状态或支付模式为现金支付
            return Response(serializer.data, status=status.HTTP_206_PARTIAL_CONTENT)
        else:
            if payment_mode == 2:     # 微信支付
                _wxPay = WXPay(obj)
                result = _wxPay.native()
                if isinstance(result, Exception):
                    return Response(result.args, status=status.HTTP_400_BAD_REQUEST)
                return Response({'code_url': result},
                                status=status.HTTP_206_PARTIAL_CONTENT)
            else:     # 支付宝支付
                return Response({}, status=status.HTTP_206_PARTIAL_CONTENT)


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
        return Orders.get_objects_list(request, **kwargs)

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


class SaleList(generics.GenericAPIView):
    queryset = Orders.objects.all()
    serializer_class = OrdersSerializer
    permissions = (IsOwnerOrReadOnly,)

    def get_objects_list(self, request, **kwargs):
        return get_sale_list(request, **kwargs)

    def post(self, request, *args, **kwargs):
        form = SaleListForm(request.data)
        if not form.is_valid():
            return Response(form.errors, status=status.HTTP_400_BAD_REQUEST)

        cld = form.cleaned_data
        for key in cld.keys():
            if not cld[key]:
                cld.pop(key)

        object_data = self.get_objects_list(request, **cld)
        if isinstance(object_data, Exception):
            return Response({'Error': object_data.args}, status=status.HTTP_400_BAD_REQUEST)

        serializer = SaleListSerializer(data=object_data)
        if serializer.is_valid():
            results = serializer.list_data(**cld)
            if isinstance(results, Exception):
                return Response({'Error': results.args}, status=status.HTTP_400_BAD_REQUEST)
            return Response(results, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
