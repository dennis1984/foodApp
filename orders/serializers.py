#-*- coding:utf8 -*-
from orders.models import Orders
from rest_framework import serializers
from horizon.serializers import BaseListSerializer, timezoneStringTostring


class OrdersSerializer(serializers.ModelSerializer):
    class Meta:
        model = Orders
        # fields = ('id', 'orders_id', 'user_id', 'city', 'meal_center',
        #           'meal_ids', 'payable', 'payment_status', 'extend')
        fields = '__all__'

    def update_payment_status(self, instance, validated_data):
        super(OrdersSerializer, self).update(
            instance,
            {'payment_status': validated_data['validated_data']}
        )

    @property
    def data(self):
        serializer = super(OrdersSerializer, self).data
        serializer['updated'] = timezoneStringTostring(serializer['updated'])
        serializer['created'] = timezoneStringTostring(serializer['created'])
        return serializer


class OrdersListSerializer(BaseListSerializer):
    child = OrdersSerializer()


class SaleSerializer(serializers.Serializer):
    date = serializers.CharField()
    total_count = serializers.IntegerField()
    total_payable = serializers.CharField()


class SaleListSerializer(BaseListSerializer):
    child = SaleSerializer()

