# -*- coding: utf8 -*-
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from horizon import main
from PAY.alipay.models import AliPayResult
from PAY.alipay.serializers import PreCreateResponseSerializer
from PAY.wxpay.views import api_settings
from PAY.alipay.forms import PreCreateCallbackForm
from orders.models import Orders
from decimal import Decimal
import json
import copy


class PreCreateCallback(APIView):
    authentication_classes = api_settings.PAY_CALLBACK_AUTHENTICATION_CLASSES
    permission_classes = api_settings.PAY_CALLBACK_PERMISSION_CLASSES

    def __init__(self, **kwargs):
        self._orders_id = None
        self._ali_instance = None
        super(PreCreateCallback, self).__init__(**kwargs)

    def post(self, request, *args, **kwargs):
        """
        支付宝支付回调请求
        :param request:
        :return:
        """
        success_message = {'return_code': 'SUCCESS',
                           'return_msg': 'OK'}
        fail_message = {'return_code': 'FAIL',
                        'return_msg': 'SIGN INCORRECT'}
        success_data = {'payment_status': 200,
                        'payment_mode': 3}
        fail_data = {'payment_status': 500,
                     'payment_code': 3}

        form = PreCreateCallbackForm(request.data)
        if not form.is_valid():
            return Response(fail_message, status=status.HTTP_200_OK)

        self.request_data = _request_data = form.cleaned_data
        if not self.is_sign_valid():
            return Response(fail_message, status=status.HTTP_200_OK)

        if _request_data['trade_status'] == 'TRADE_SUCCESS':
            try:
                Orders.update_payment_status_by_pay_callback(
                    orders_id=self._orders_id,
                    validated_data=success_data)
            except:
                return Response(success_message, status=status.HTTP_200_OK)
        else:
            try:
                Orders.update_payment_status_by_pay_callback(
                    orders_id=self._orders_id,
                    validated_data=fail_data)
            except:
                return Response(success_message, status=status.HTTP_200_OK)
        serializer = PreCreateResponseSerializer(self._ali_instance)
        serializer.update_alipay_result(self._ali_instance, _request_data)
        return Response(success_message,  status=status.HTTP_200_OK)

    def is_sign_valid(self):
        """
        验证签名有效性
        return: Boolean
        """
        orders_id = self.request_data['out_trade_no']
        instance = AliPayResult.get_object_by_orders_id(orders_id)
        if isinstance(instance, Exception):
            return False

        if not self._orders_id:
            self._orders_id = orders_id
        if not self._ali_instance:
            self._ali_instance = instance

        param_dict = json.loads(instance.request_data)
        biz_content = json.loads(param_dict['biz_content'])
        if Decimal(str(biz_content['total_amount'])) != \
                Decimal(self.request_data['total_amount']) != \
                Decimal(self.request_data['receipt_amount ']):
            return False
        sign = self.request_data.pop('sign')
        self.request_data.pop('sign_type')
        params_str = main.make_dict_to_verify_string(self.request_data)

        return main.verify_sign_for_alipay(params_str, sign)
