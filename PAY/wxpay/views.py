# -*- coding: utf8 -*-
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.settings import APISettings, DEFAULTS, IMPORT_STRINGS

from horizon import main
from PAY.wxpay.models import WXPayResult
from PAY.wxpay.serializers import NativeResponseSerializer
from orders.models import Orders
import json
import copy


_default = copy.deepcopy(DEFAULTS)
_default.update(**{
    'PAY_CALLBACK_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.BasicAuthentication',
        'rest_framework.authentication.SessionAuthentication',),
    'PAY_CALLBACK_PERMISSION_CLASSES': (
        'rest_framework.permissions.AllowAny',
    )})
_import_strings = list(copy.deepcopy(IMPORT_STRINGS))
_import_strings.extend(['PAY_CALLBACK_AUTHENTICATION_CLASSES',
                        'PAY_CALLBACK_PERMISSION_CLASSES'])

api_settings = APISettings(None, _default, _import_strings)

WXPAY_REQUEST_DATA = ('appid', 'mch_id', 'nonce_str', 'sign', 'result_code',
                      'openid', 'trade_type', 'bank_type', 'total_fee',
                      'cash_fee', 'transaction_id', 'out_trade_no', 'time_end')


class NativeCallback(APIView):
    authentication_classes = api_settings.PAY_CALLBACK_AUTHENTICATION_CLASSES
    permission_classes = api_settings.PAY_CALLBACK_PERMISSION_CLASSES

    def __init__(self, **kwargs):
        self._orders_id = None
        self._wx_instance = None
        super(NativeCallback, self).__init__(**kwargs)

    def post(self, request, *args, **kwargs):
        """
        微信支付回调请求
        :param request:
        :return:
        """
        return_msg = {'return_code': 'SUCCESS',
                      'return_msg': 'OK'}
        update_data = {'payment_status': 200,
                       'payment_mode': 2}

        data_dict = main.anaysize_xml_to_dict(request.body)
        # 微信支付时返回通讯失败
        if data_dict['return_code'] == 'FAIL':
            return Response(main.make_dict_to_xml({'return_code': 'FAIL',
                                                   'return_msg': 'ERROR'}),
                            status=status.HTTP_200_OK)
        if not self.is_sign_valid(data_dict):
            return Response(main.make_dict_to_xml({'return_code': 'FAIL',
                                                   'return_msg': 'SIGN INCORRECT'}),
                            status=status.HTTP_200_OK)

        if data_dict['result_code'] == 'SUCCESS':
            try:
                Orders.update_payment_status_by_pay_callback(orders_id=self._orders_id,
                                                             validated_data=update_data)
            except:
                pass
        else:
            try:
                Orders.update_payment_status_by_pay_callback(orders_id=self._orders_id,
                                                             validated_data={'payment_status': 500,
                                                                             'payment_code': 2})
            except:
                pass
        serializer = NativeResponseSerializer(self._wx_instance)
        try:
            serializer.update(self._wx_instance, data_dict)
        except:
            pass
        return Response(main.make_dict_to_xml(return_msg), status=status.HTTP_200_OK)

    def is_sign_valid(self, request_data):
        """
        验证签名有效性
        return: Boolean
        """
        orders_id = request_data['out_trade_no']
        instance = WXPayResult.get_object_by_orders_id(orders_id)
        if isinstance(instance, Exception):
            return False

        if not self._orders_id:
            self._orders_id = orders_id
        if not self._wx_instance:
            self._wx_instance = instance

        param_dict = json.loads(instance.request_data)
        if int(request_data['total_fee']) != int(param_dict['total_fee']):
            return False
        sign = request_data.pop('sign')

        _sign = main.make_sign_for_wxpay(request_data)
        if _sign == sign:
            return True
        else:
            return False
