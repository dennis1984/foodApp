# -*- coding: utf8 -*-
from PAY.wxpay import native, serializers as wx_serializers
from PAY.alipay import precreate, serializers as ali_serializers
from orders.models import Orders
from users.models import BusinessUser
from horizon import main
from django.conf import settings
import os
import json
from decimal import Decimal


def get_user_info(user_id):
    return BusinessUser.get_object(pk=user_id)


class WXPay(object):
    def __init__(self, instance):
        if not isinstance(instance, Orders):
            raise Exception('Initialization Error')
        self.orders_id = instance.orders_id
        self.total_fee = int(Decimal(instance.payable) * 100)
        self.kwargs = {'detail': instance.dishes_ids_json_detail}

        user_info = get_user_info(instance.user_id)
        self.body = u'%s-%s' % (user_info.business_name, instance.orders_id)

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
        self.response_params = xml_dict
        if 'code_url' not in xml_dict:
            return Exception({'Detail': xml_dict.get('err_code', xml_dict['return_msg'])})
        if not self.is_response_params_valid():
            return Exception({'Detail': 'Sign is not valid'})

        # 存入数据库
        request_data = {'orders_id': self.orders_id,
                        'request_data': json.dumps(_wxpay.__dict__)}
        serializer = wx_serializers.NativeRequestSerializer(data=request_data)
        if serializer.is_valid():
            serializer.save()
        qrcode_path = main.make_qrcode(xml_dict['code_url'])
        return os.path.join(settings.WEB_URL_FIX,
                            'static',
                            qrcode_path.split('/static/', 1)[1])

    def is_response_params_valid(self):
        """
        验证微信支付返回结果的有效性
        """
        if not isinstance(self.response_params, dict):
            return False
        _sign = self.response_params.pop('sign')
        maked_sign = main.make_sign_for_wxpay(self.response_params)

        if maked_sign == _sign:
            return True
        return False


ALIPAY_RESPONSE_KEY = 'alipay_trade_precreate_response'
ALIPAY_SIGN_KEY = 'sign'


class AliPay(object):
    def __init__(self, instance):
        if not isinstance(instance, Orders):
            raise Exception('Initialization Error')
        self.orders_id = instance.orders_id
        self.total_amount = str(instance.payable)
        self.kwargs = {'goods_detail': instance.dishes_ids_detail}

        user_info = get_user_info(instance.user_id)
        self.subject = u'%s-%s' % (user_info.business_name, instance.orders_id)

    class Meta:
        fields = ('orders_id', 'total_amount', 'subject')

    def pre_create(self):
        """
        扫描支付（预支付模式）
        """
        _alipay = precreate.AliPayPreCreate(subject=self.subject,
                                            out_trade_no=self.orders_id,
                                            total_amount=self.total_amount,
                                            **self.kwargs)
        results = _alipay.go_to_pay()
        if results.status_code != 200:
            return Exception(results.reason)

        _response_params = json.loads(results.text)
        response_data = _response_params[ALIPAY_RESPONSE_KEY]
        _sign = _response_params[ALIPAY_SIGN_KEY]

        if not response_data.get('qr_code', None):
            return Exception({'Detail': response_data.get('sub_msg', response_data['msg'])})
        if not self.is_response_params_valid(results.text, _sign):
            return Exception({'Detail': 'Sign is not valid'})

        # 存入数据库
        request_data = {'orders_id': self.orders_id,
                        'request_data': json.dumps(_alipay.request_data)}
        serializer = ali_serializers.PreCreateRequestSerializer(data=request_data)
        if serializer.is_valid():
            serializer.save()
        qrcode_path = main.make_qrcode(response_data['qr_code'])
        return os.path.join(settings.WEB_URL_FIX,
                            'static',
                            qrcode_path.split('/static/', 1)[1])

    def is_response_params_valid(self, json_params, _sign):
        """
        验证支付宝返回结果的有效性
        """
        params_str = json_params.split(':', 1)[1]
        params_str = params_str.split('}', 1)[0]
        params_str = '%s}' % params_str
        is_valid = main.verify_sign_for_alipay(params_str, source_sign=_sign)

        if is_valid:
            return True
        return False

