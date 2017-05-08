from django.shortcuts import render
from rest_framework.viewsets import ModelViewSet
from orders.models import Orders
from orders.serializers import OrdersSerializer


class OrdersViewSet(OrdersSerializer):
    queryset = Orders.objects.all()
    serializer_class = OrdersSerializer