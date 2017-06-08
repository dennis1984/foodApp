#-*- coding:utf8 -*-
from PAY.alipay.models import AliPayResult
from rest_framework import serializers


class PreCreateRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = AliPayResult
        fields = ('orders_id', 'request_data', 'extend')


class PreCreateResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = AliPayResult
        fields = ('trade_status', 'subject', 'body', 'trade_no', 'app_id',
                  'out_trade_no', 'total_amount', 'receipt_amount', 'out_biz_no',
                  'open_id', 'buyer_logon_id', 'buyer_id', 'seller_id', 'seller_email',
                  'gmt_create', 'gmt_payment', 'gmt_refund', 'gmt_close',
                  'invoice_amount', 'buyer_pay_amount', 'point_amount', 'refund_fee',
                  'fund_bill_list', 'voucher_detail_list')

    def update_alipay_result(self, instance, validated_data):
        """
        微信回调信息写入数据库
        """
        try:
            return super(PreCreateResponseSerializer, self).update(instance, validated_data)
        except Exception as e:
            return e


