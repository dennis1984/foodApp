# -*- coding: utf8 -*-
from rest_framework.parsers import JSONParser
from rest_framework import status
from rest_framework.response import Response

from rest_framework import generics
from django.utils.six import BytesIO
from django.conf import settings
from orders.forms import (OrdersInputForm,
                          OrdersGetForm,
                          OrdersUpdateForm,
                          OrdersListForm,
                          VerifyOrdersListForm,
                          VerifyOrdersActionForm,
                          VerifyOrdersDetailForm,
                          SaleListForm)
from orders.models import (Orders,
                           SaleListAction,
                           VerifyOrders,
                           YinshiPayCode,
                           ORDERS_PAYMENT_MODE)
from orders.serializers import (OrdersSerializer,
                                OrdersListSerializer,
                                VerifyOrdersListSerializer,
                                VerifySerializer,
                                OrdersDetailSerializer,
                                SaleOrdersListSerializer,
                                SaleDishesListSerializer,
                                YinshiPayCodeSerializer)
from orders.permissoins import IsOwnerOrReadOnly
from orders.pays import WXPay, AliPay
from Consumer_App.cs_orders.models import ConfirmConsume
from horizon import main

import json


class OrdersAction(generics.GenericAPIView):
    queryset = Orders.objects.all()
    serializer_class = OrdersSerializer

    def get_orders_detail(self, instance):
        return Orders.make_instances_to_dict(instance)[0]

    def make_perfect_dishes_ids(self, orders):
        perfect_ids = []
        for item in json.loads(orders.dishes_ids):
            tmp_dict = {'dishes_id': item['id'],
                        'count': item['count']}
            perfect_ids.append(tmp_dict)
        return perfect_ids

    def make_yinshi_pay_initial_data(self, request,  orders):
        random_code = main.make_random_string_char_and_number(20)
        data = {'dishes_ids': json.dumps(self.make_perfect_dishes_ids(orders)),
                'user_id': request.user.id,
                'code': random_code,
                'business_orders_id': orders.orders_id}
        return data

    def save_yinshi_pay_random_code(self, initial_data):
        serializer = YinshiPayCodeSerializer(data=initial_data)
        if not serializer.is_valid():
            return Exception(serializer.errors)
        try:
            serializer.save()
        except Exception as e:
            return e
        return serializer.instance

    def get_yinshi_pay_response(self, ys_pay_instance):
        ys_code_url = settings.YINSHI_PAY_LINK % ys_pay_instance.code
        file_name = main.make_qrcode(ys_code_url, logo_name='yspay')
        return_data = {
            'code': ys_pay_instance.code,
            'ys_code_url': main.make_static_url_by_file_path(file_name)
        }
        return return_data

    def post(self, request, *args, **kwargs):
        """
        :param request: 
        :param args: 
        :param kwargs: {'dishes_ids': [{'dishes_id': '',
                                       'count': '',
                                       }, ...
                                       ],
                        }
        :return: 
        """
        form = OrdersInputForm(request.data)
        if not form.is_valid():
            return Response(form.errors, status=status.HTTP_400_BAD_REQUEST)

        cld = form.cleaned_data
        stream = BytesIO(cld['dishes_ids'])
        dishes_ids = JSONParser().parse(stream)

        object_data = Orders.make_orders_by_dishes_ids(request, dishes_ids=dishes_ids)
        if isinstance(object_data, Exception):
            return Response({'Detail': object_data.args}, status=status.HTTP_400_BAD_REQUEST)

        serializer = OrdersSerializer(data=object_data)
        if serializer.is_valid():
            serializer.save()

            orders_detail = self.get_orders_detail(serializer.instance)
            res_serializer = OrdersDetailSerializer(data=orders_detail)
            if not res_serializer.is_valid():
                return Response({'Detail': res_serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
            return Response(res_serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, *args, **kwargs):
        """
        更新订单状态
        :param request:
        :param args:
        :param kwargs: 'order_id': 订单ID
                       'payment_status': 订单支付状态
                       'payment_mode': 订单支付方式
        :return: Orders instance
        """
        form = OrdersUpdateForm(request.data)
        if not form.is_valid():
            return Response({'Detail': form.errors}, status=status.HTTP_400_BAD_REQUEST)

        cld = form.cleaned_data
        obj = Orders.get_object(**{'orders_id': cld['orders_id']})
        if isinstance(obj, Exception):
            return Response({'Detail': obj.args}, status=status.HTTP_400_BAD_REQUEST)

        serializer = OrdersSerializer(obj)
        try:
            serializer.update_orders_status(obj, cld)
        except Exception as e:
            return Response({'Detail': e.args}, status=status.HTTP_400_BAD_REQUEST)

        payment_mode = cld['payment_mode']
        if cld.get('payment_status'):
            # 更新支付状态为现金支付
            res_serializer = OrdersDetailSerializer(data=serializer.data)
            if not res_serializer.is_valid():
                return Response({'Detail': res_serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
            return Response(res_serializer.data, status=status.HTTP_206_PARTIAL_CONTENT)
        else:
            if payment_mode == 'cash':     # 现金支付
                res_serializer = OrdersDetailSerializer(data=serializer.data)
                if not res_serializer.is_valid():
                    return Response({'Detail': res_serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
                return Response(res_serializer.data, status=status.HTTP_206_PARTIAL_CONTENT)
            elif payment_mode == 'scan':     # 扫码支付
                _wxPay = WXPay(obj)
                wx_result = _wxPay.native()
                if isinstance(wx_result, Exception):
                    return Response(wx_result.args, status=status.HTTP_400_BAD_REQUEST)

                _alipay = AliPay(obj)
                ali_result = _alipay.pre_create()
                if isinstance(ali_result, Exception):
                    return Response(ali_result.args, status=status.HTTP_400_BAD_REQUEST)
                return Response({'ali_code_url': ali_result,
                                 'wx_code_url': wx_result},
                                status=status.HTTP_206_PARTIAL_CONTENT)
            elif payment_mode == 'yinshi':  # 吟食支付
                data = self.make_yinshi_pay_initial_data(request, obj)
                instance = self.save_yinshi_pay_random_code(data)
                if isinstance(instance, Exception):
                    return Response({'Detail': instance.args}, status=status.HTTP_400_BAD_REQUEST)
                return_data = self.get_yinshi_pay_response(instance)
                return Response(return_data, status=status.HTTP_206_PARTIAL_CONTENT)
            else:
                return Response(status=status.HTTP_204_NO_CONTENT)


class OrdersDetail(generics.GenericAPIView):
    queryset = Orders.objects.all()
    serializer_class = OrdersSerializer

    def get_detail(self, **kwargs):
        return Orders.get_detail(**kwargs)

    def post(self, request, *args, **kwargs):
        """
        :param request:
        :param args:
        :param kwargs: {'orders_id': '',
                        }
        :return:
        """
        form = OrdersGetForm(request.data)
        if not form.is_valid():
            return Response(form.errors, status=status.HTTP_400_BAD_REQUEST)

        cld = form.cleaned_data
        detail = self.get_detail(**cld)
        if isinstance(detail, Exception):
            return Response({'Detail': detail.args}, status=status.HTTP_400_BAD_REQUEST)
        serializer = OrdersDetailSerializer(data=detail)
        if not serializer.is_valid():
            return Response({'Detail': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.data, status=status.HTTP_200_OK)


class OrdersList(generics.GenericAPIView):
    permissions = (IsOwnerOrReadOnly,)

    def get_all_list(self, request, cld):
        pay_orders = self.get_pay_list(request, cld)
        consume_orders = self.get_consume_list(request, cld)
        finished_orders = self.get_finished_list(request, cld)
        orders_list = pay_orders + consume_orders + finished_orders
        return sorted(orders_list, key=lambda x: x['created'], reverse=True)

    def get_pay_list(self, request, cld):
        return Orders.filter_paying_orders_list(request, **cld)

    def get_consume_list(self, request, cld):
        return VerifyOrders.filter_consuming_orders_list(
            request,
            set_payment_mode=ORDERS_PAYMENT_MODE['yspay'],
            **cld
        )

    def get_finished_list(self, request, cld):
        business_orders = Orders.filter_finished_orders_list(request, **cld)
        verify_orders = VerifyOrders.filter_finished_orders_list(
            request,
            set_payment_mode=ORDERS_PAYMENT_MODE['yspay'],
            **cld
        )
        orders_list = business_orders + verify_orders
        return sorted(orders_list, key=lambda key: key['created'], reverse=True)

    def get_orders_list(self, request, cld):
        _filter = cld.get('filter', 'all')
        if _filter == 'all':
            return self.get_all_list(request, cld)
        elif _filter == 'pay':
            return self.get_pay_list(request, cld)
        elif _filter == 'consume':
            return self.get_consume_list(request, cld)
        elif _filter == 'finished':
            return self.get_finished_list(request, cld)

    def post(self, request, *args, **kwargs):
        """
        :param request:
        :param args:
        :param kwargs: {'orders_id': '',
                        }
        :return:
        """
        form = OrdersListForm(request.data)
        if not form.is_valid():
            return Response(form.errors, status=status.HTTP_400_BAD_REQUEST)

        cld = form.cleaned_data
        object_data = self.get_orders_list(request, cld)
        if isinstance(object_data, Exception):
            return Response({'Detail': object_data.args}, status=status.HTTP_400_BAD_REQUEST)

        serializer = OrdersListSerializer(data=object_data)
        if not serializer.is_valid():
            return Response({'Detail': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        results = serializer.list_data(**cld)
        if isinstance(results, Exception):
            return Response({'Detail': results.args}, status=status.HTTP_400_BAD_REQUEST)
        return Response(results, status=status.HTTP_200_OK)


class VerifyOrdersList(generics.GenericAPIView):
    """
    获取核销订单信息
    """
    permissions = (IsOwnerOrReadOnly,)

    def get_verify_orders_list(self, request, consumer_id):
        kwargs = {'consumer_id': consumer_id}
        return VerifyOrders.filter_consuming_orders_list(request=request, gateway='verify', **kwargs)

    def is_request_data_valid(self, request):
        form = VerifyOrdersListForm(request.data)
        if not form.is_valid():
            return False, Exception(form.errors)

        cld = form.cleaned_data
        return True, cld

    def get_verfify_orders_detail(self, request, **cld):
        # 待核销订单
        if 'gateway' not in cld or cld['gateway'] == 'confirm_consume':
            instance = ConfirmConsume.get_object(random_string=cld['random_string'])
            if isinstance(instance, Exception):
                return instance
            return self.get_verify_orders_list(request, consumer_id=instance.user_id)
        # 吟食支付订单
        else:
            instance = YinshiPayCode.get_object(code=cld['random_string'])
            if isinstance(instance, Exception):
                return instance
            return VerifyOrders.filter_finished_orders_list(request,
                                                            orders_id=instance.consume_orders_id)

    def post(self, request, *args, **kwargs):
        is_valid, cleaned_data = self.is_request_data_valid(request)
        if not is_valid:
            return Response({'Detail': cleaned_data.args}, status=status.HTTP_400_BAD_REQUEST)

        orders_data = self.get_verfify_orders_detail(request, **cleaned_data)
        if isinstance(orders_data, Exception):
            return Response({'Detail': orders_data.args}, status=status.HTTP_400_BAD_REQUEST)

        serializer = VerifyOrdersListSerializer(data=orders_data)
        if not serializer.is_valid():
            return Response({'Detail': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        results = serializer.list_data()
        if isinstance(results, Exception):
            return Response({'Detail': results.args}, status=status.HTTP_400_BAD_REQUEST)
        return Response(results, status=status.HTTP_200_OK)


class VerifyOrdersAction(generics.GenericAPIView):
    """
    核销订单
    """
    def get_verify_orders_list(self, request, cld):
        random_kwargs = {'random_string': cld['random_string']}
        random_instance = ConfirmConsume.get_object(**random_kwargs)
        if isinstance(random_instance, Exception):
            return random_instance

        orders_kwargs = {'consumer_id': random_instance.user_id}
        orders_list = VerifyOrders.filter_consuming_orders_list(request=request,
                                                                is_detail=False,
                                                                gateway='verify',
                                                                **orders_kwargs)
        orders_ids_all = [orders.orders_id for orders in orders_list]
        for orders_id in cld['orders_ids']:
            if orders_id not in orders_ids_all:
                return Exception('Params [orders_ids] data error')

        verify_orders = []
        for orders in orders_list:
            if orders.orders_id in cld['orders_ids']:
                verify_orders.append(orders)
        return verify_orders

    def get_orders_detail(self, instances):
        return VerifyOrders.make_instances_to_dict(instances)

    def is_request_data_valid(self, request):
        form = VerifyOrdersActionForm(request.data)
        if not form.is_valid():
            return False, Exception(form.errors)

        cld = form.cleaned_data
        try:
            orders_ids = json.loads(cld['orders_ids'])
        except Exception as e:
            return False, e
        cld['orders_ids'] = orders_ids
        return True, cld

    def put(self, request, *args, **kwargs):
        is_valid, cld = self.is_request_data_valid(request)
        if not is_valid:
            return Response({'Detail': cld.args}, status=status.HTTP_400_BAD_REQUEST)

        results = self.get_verify_orders_list(request, cld)
        if isinstance(results, Exception):
            return Response({'Detail': results.args}, status=status.HTTP_400_BAD_REQUEST)

        serializer = VerifySerializer()
        result_data = serializer.confirm_consume(request, results, **cld)
        if isinstance(result_data, Exception):
            return Response({'Detail': result_data.args}, status=status.HTTP_400_BAD_REQUEST)

        orders_detail = self.get_orders_detail(result_data)
        serializer = VerifyOrdersListSerializer(data=orders_detail)
        if not serializer.is_valid():
            return Response({'Detail': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        datas = serializer.list_data()
        if isinstance(datas, Exception):
            return Response({'Detail': datas.args}, status=status.HTTP_400_BAD_REQUEST)
        return Response(datas, status=status.HTTP_200_OK)
        # return Response({'result': 'SUCCESS'}, status=status.HTTP_206_PARTIAL_CONTENT)


class VerifyOrdersDetail(generics.GenericAPIView):
    """
    获取吟食支付核销订单详情
    """
    permissions = (IsOwnerOrReadOnly,)

    def is_request_data_valid(self, request):
        form = VerifyOrdersDetailForm(request.data)
        if not form.is_valid():
            return False, Exception(form.errors)

        cld = form.cleaned_data
        return True, cld

    def get_verfify_orders_detail(self, request, **cld):
        # 吟食支付订单
        instance = YinshiPayCode.get_object(code=cld['random_string'])
        if isinstance(instance, Exception):
            return instance
        instances = VerifyOrders.filter_finished_orders_list(
            request,
            orders_id=instance.consume_orders_id
        )
        if isinstance(instances, Exception):
            return instances
        return instances[0]

    def post(self, request, *args, **kwargs):
        is_valid, cleaned_data = self.is_request_data_valid(request)
        if not is_valid:
            return Response({'Detail': cleaned_data.args}, status=status.HTTP_400_BAD_REQUEST)

        orders_data = self.get_verfify_orders_detail(request, **cleaned_data)
        if isinstance(orders_data, Exception):
            return Response({}, status=status.HTTP_400_BAD_REQUEST)

        serializer = OrdersDetailSerializer(data=orders_data)
        if not serializer.is_valid():
            return Response({'Detail': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.data, status=status.HTTP_200_OK)


class SaleOrdersList(generics.GenericAPIView):
    permissions = (IsOwnerOrReadOnly,)

    def get_objects_list(self, request, **kwargs):
        return SaleListAction.get_sale_list(request, **kwargs)

    def post(self, request, *args, **kwargs):
        form = SaleListForm(request.data)
        if not form.is_valid():
            return Response(form.errors, status=status.HTTP_400_BAD_REQUEST)

        cld = form.cleaned_data
        object_data = self.get_objects_list(request, **cld)
        if isinstance(object_data, Exception):
            return Response({'Detail': object_data.args}, status=status.HTTP_400_BAD_REQUEST)

        serializer = SaleOrdersListSerializer(data=object_data)
        if serializer.is_valid():
            results = serializer.list_data(**cld)
            if isinstance(results, Exception):
                return Response({'Detail': results.args}, status=status.HTTP_400_BAD_REQUEST)
            return Response(results, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SaleDishesList(generics.GenericAPIView):
    permissions = (IsOwnerOrReadOnly,)

    def get_objects_list(self, request, **kwargs):
        return SaleListAction.get_dishes_sale_list(request, **kwargs)

    def post(self, request, *args, **kwargs):
        form = SaleListForm(request.data)
        if not form.is_valid():
            return Response(form.errors, status=status.HTTP_400_BAD_REQUEST)

        cld = form.cleaned_data
        object_data = self.get_objects_list(request, **cld)
        if isinstance(object_data, Exception):
            return Response({'Detail': object_data.args}, status=status.HTTP_400_BAD_REQUEST)

        serializer = SaleDishesListSerializer(data=object_data)
        if serializer.is_valid():
            results = serializer.list_data(**cld)
            if isinstance(results, Exception):
                return Response({'Detail': results.args}, status=status.HTTP_400_BAD_REQUEST)
            return Response(results, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
