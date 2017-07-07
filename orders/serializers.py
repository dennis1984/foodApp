# -*- coding:utf8 -*-
from orders.models import Orders, VerifyOrders
from rest_framework import serializers
from horizon.serializers import (BaseListSerializer,
                                 BaseSerializer,
                                 BaseModelSerializer)
from django.utils.timezone import now


class OrdersSerializer(BaseModelSerializer):
    class Meta:
        model = Orders
        fields = '__all__'

    def update_orders_status(self, instance, validated_data):
        if instance.payment_status != 0:
            raise Exception('The orders already paid or expired!')

        if validated_data['payment_mode'] == 'cash':
            validated_data['payment_mode'] = 1
        else:
            if 'payment_status' in validated_data:
                validated_data.pop('payment_status')

        if validated_data.get('payment_status', None):
            return self.update_payment_status(instance, validated_data)
        else:
            return self.update_payment_mode(instance, validated_data)

    def update_payment_status(self, instance, validated_data):
        """
        更新订单支付状态（仅适用于现金支付）
        """
        payment_status = validated_data['payment_status']
        payment_mode = validated_data['payment_mode']
        if payment_status != 200:
            raise ValueError('Payment status must be 200')
        if payment_mode == 1:           # 现金支付
            return super(OrdersSerializer, self).update(
                instance,
                {'payment_status': payment_status,
                 'payment_mode': payment_mode}
            )
        else:
            return instance

    def update_payment_status_by_pay_callback(self, instance, validated_data):
        """
        更新订单支付状态（仅适用于微信支付和支付宝支付）
        """
        payment_status = validated_data['payment_status']
        payment_mode = validated_data['payment_mode']

        if instance.payment_status != 0:
            raise Exception('Cannot perform the action.')
        if payment_status not in (200, 400, 500):
            raise ValueError('Payment status must in range [200, 400, 500]')

        if payment_mode in [2, 3]:           # 微信支付，支付宝支付
            return super(OrdersSerializer, self).update(
                instance,
                {'payment_status': payment_status,
                 'payment_mode': payment_mode}
            )
        else:
            return instance

    def update_payment_mode(self, instance, validated_data):
        """
        更新订单支付方式
        """
        return instance


class OrdersListSerializer(BaseListSerializer):
    child = OrdersSerializer()


class SaleSerializer(BaseSerializer):
    date = serializers.CharField()
    total_count = serializers.IntegerField()
    total_payable = serializers.CharField()
    business_name = serializers.CharField(required=False)
    user_id = serializers.IntegerField(required=False)


class SaleListSerializer(BaseListSerializer):
    child = SaleSerializer()


class DishesIdsDetailSerializer(BaseSerializer):
    count = serializers.IntegerField()
    id = serializers.IntegerField()
    is_recommend = serializers.BooleanField()
    price = serializers.CharField()
    size = serializers.IntegerField()
    title = serializers.CharField()
    user_id = serializers.IntegerField()


class VerifySerializer(BaseModelSerializer):
    class Meta:
        model = VerifyOrders
        fields = '__all__'

