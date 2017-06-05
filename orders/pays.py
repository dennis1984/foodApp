# -*- coding: utf8 -*-
from PAY.wxpay import native, serializers
from orders.models import Orders
from horizon import main
from django.conf import settings
import os
import json
from decimal import Decimal


class WXPay(object):
    def __init__(self, instance):
        if not isinstance(instance, Orders):
            raise Exception('Initialization Error')
        self.orders_id = instance.orders_id
        self.total_fee = int(Decimal(instance.payable) * 100)
        self.kwargs = {'detail': instance.dishes_ids_json_detail}
        self.body = u'吟食支付'

    def native(self):
        """
        扫描支付（统一下单模式）
        """
        _wxpay = native.WXPAYNative(body=self.body,
                                    out_trade_no=self.orders_id,
                                    total_fee=self.total_fee,
                                    **self.kwargs)
        results = _wxpay.go_to_pay()
        if results.status_code != 200:
            return Exception(results.reason)
        # 解析xml
        xml_dict = main.anaysize_xml_to_dict(results.text)
        if 'code_url' not in xml_dict:
            return Exception({'Detail': xml_dict.get('err_code', 'Result error')})

        # 存入数据库
        request_data = {'orders_id': self.orders_id,
                        'request_data': json.dumps(_wxpay.__dict__)}
        serializer = serializers.NativeRequestSerializer(data=request_data)
        if serializer.is_valid():
            serializer.save()
        qrcode_path = main.make_qrcode(xml_dict['code_url'])
        return os.path.join(settings.WEB_URL_FIX,
                            'static',
                            qrcode_path.split('/static/', 1)[1])
