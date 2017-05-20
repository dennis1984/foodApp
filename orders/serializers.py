#-*- coding:utf8 -*-
from orders.models import Orders
from rest_framework import serializers
from dishes.serializers import timezoneStringTostring
from dishes.models import FoodCourt


class OrdersSerializer(serializers.ModelSerializer):
    class Meta:
        model = Orders
        # fields = ('id', 'orders_id', 'user_id', 'city', 'meal_center',
        #           'meal_ids', 'payable', 'payment_status', 'extend')
        fields = '__all__'

    # def create(self, orders_data):
    #     return Orders.objects.create(**orders_data)
    #
    # def update(self, instance, orders_data):
    #     instance.save()
    #     return instance
    def update_payment_status(self, instance, validated_data):
        super(OrdersSerializer, self).update(instance,
                                             {'payment_status': validated_data['validated_data']})

    @property
    def data(self):
        serializer = super(OrdersSerializer, self).data
        serializer['orders_id'] = ordersIdIntegerToString(serializer['id'])
        serializer['updated'] = timezoneStringTostring(serializer['updated'])
        serializer['created'] = timezoneStringTostring(serializer['created'])
        return serializer


def ordersIdIntegerToString(orders_id):
    if len(str(orders_id)) < 8:
        return "%08d" % orders_id
    return str(orders_id)

