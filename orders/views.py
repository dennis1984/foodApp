# -*- coding: utf8 -*-

from rest_framework.viewsets import ModelViewSet

from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.renderers import JSONRenderer
from rest_framework.parsers import JSONParser
from orders.models import Orders
from orders.serializers import OrdersSerializer

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework import permissions
from rest_framework.response import Response

from rest_framework import mixins
from rest_framework import generics
from orders.forms import OrdersInputForm


class OrdersList(mixins.CreateModelMixin, generics.GenericAPIView):
    queryset = Orders.objects.all()
    serializer_class = OrdersSerializer

    def post(self, request, *args, **kwargs):
        """
        :param request: 
        :param args: 
        :param kwargs: {'city': '', 
                        'meal_center': '',
                        'dishes_ids': {'dishes_id': '',
                                       'count': '',
                                       },
                        }
        :return: 
        """
        form = OrdersInputForm(request.data)
        if not form.is_valid():
            return Response(request.data, status=status.HTTP_400_BAD_REQUEST)

        cld = form.cleaned_data
        dishes_ids = JSONRenderer().render(cld['dishes_ids'])

        return Response(dishes_ids)

        # return self.create(request, *args, **kwargs)


class OrdersViewSet(ModelViewSet):
    queryset = Orders.objects.all()
    serializer_class = OrdersSerializer


class JSONResponse(HttpResponse):
    def __init__(self, data, **kwargs):
        content = JSONRenderer().render(data)
        kwargs['content_type'] = 'application/json'
        super(JSONResponse, self).__init__(content, **kwargs)


# @api_view(['GET', 'POST'])
# @permission_classes((permissions.AllowAny,))
# # @csrf_exempt
# def order_list(request, format=None):
#     """
#     展示所有订单，或创建订单
#     """
#     if request.method == 'GET':
#         orders_list = Orders.objects.all()
#         serializer = OrdersSerializer(orders_list, many=True)
#         # return JSONResponse(serializer.data)
#         return Response(serializer.data)


# class OrderList(mixins.ListModelMixin, mixins.CreateModelMixin,
#                 generics.GenericAPIView):
# class OrderList(generics.ListAPIView, generics.GenericAPIView):
#     # def get(self, request, format=None):
#     #     orders_list = Orders.objects.all()
#     #     serializer = OrdersSerializer(orders_list, many=True)
#     #     return Response(serializer.data)
#
#     queryset = Orders.objects.all()
#     serializer_class = OrdersSerializer

    # def get(self, request, *args, **kwargs):
    #     return self.list(request, *args, **kwargs)


@csrf_exempt
def save_order(request):
    if request.method == 'GET':
        data = JSONParser().parse(request)
        serializer = OrdersSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return JSONResponse(serializer.data, status=201)
        return JSONResponse(serializer.errors, status=400)
