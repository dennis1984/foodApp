#-*- coding:utf8 -*-
from PAY.wxpay.models import WXPayResult
from rest_framework import serializers
from django.core.paginator import Paginator
from django.conf import settings
from horizon.serializers import BaseListSerializer, timezoneStringTostring
import datetime, os


class NativeRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = WXPayResult
        fields = ('orders_id', 'request_data', 'extend')
        # fields = '__all__'


class NativeResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = WXPayResult
        fields = ('result_code', 'err_code', 'err_code_des', 'openid', 'is_subscribe',
                  'trade_type', 'bank_type', 'total_fee', 'settlement_total_fee',
                  'cash_fee', 'transaction_id', 'attach', 'time_end')

    def update_wxpay_result(self, instance, validated_data):
        """
        微信回调信息写入数据库
        """
        return super(NativeResponseSerializer, self).update(instance, validated_data)


