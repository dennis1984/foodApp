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
from orders.forms import OrdersInputForm, OrdersGetForm
from orders.models import Orders
from orders.serializers import OrdersSerializer


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
            return Response(request.data, status=status.HTTP_400_BAD_REQUEST)

        cld = form.cleaned_data
        stream = BytesIO(cld['dishes_ids'])
        dishes_ids = JSONParser().parse(stream)

        object_data = Orders.make_orders_by_dishes_ids(request, dishes_ids=dishes_ids)
        serializer = OrdersSerializer(data=object_data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OrdersDetail(generics.GenericAPIView, mixins.RetrieveModelMixin):
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

        object_data = self.get_object(**cld)
        serializer = OrdersSerializer(object_data)
        return Response(serializer.data, status=status.HTTP_200_OK)


# @csrf_exempt
# def save_order(request):
#     if request.method == 'GET':
#         data = JSONParser().parse(request)
#         serializer = OrdersSerializer(data=data)
#         if serializer.is_valid():
#             serializer.save()
#             return JSONResponse(serializer.data, status=201)
#         return JSONResponse(serializer.errors, status=400)
