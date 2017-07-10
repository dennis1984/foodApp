# -*- coding: utf8 -*-
from rest_framework.parsers import JSONParser
from rest_framework import status
from rest_framework.response import Response

from rest_framework import generics
from django.utils.six import BytesIO
from orders.forms import (OrdersInputForm,
                          OrdersGetForm,
                          OrdersUpdateForm,
                          OrdersListForm,
                          VerifyOrdersListForm,
                          VerifyOrdersActionForm,
                          SaleListForm)
from orders.models import (Orders,
                           SaleListAction,
                           VerifyOrders)
from orders.serializers import (OrdersSerializer,
                                OrdersListSerializer,
                                VerifyOrdersListSerializer,
                                VerifySerializer,
                                VerifyOrdersActionResponseSerializer,
                                SaleListSerializer)
from orders.permissoins import IsOwnerOrReadOnly
from orders.pays import WXPay, AliPay
from Consumer_App.cs_orders.models import ConfirmConsume


class OrdersAction(generics.GenericAPIView):
    queryset = Orders.objects.all()
    serializer_class = OrdersSerializer

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
            return Response(serializer.data, status=status.HTTP_201_CREATED)
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
            return Response(serializer.data, status=status.HTTP_206_PARTIAL_CONTENT)
        else:
            if payment_mode == 'cash':     # 现金支付
                return Response({'code_url': ''},
                                status=status.HTTP_206_PARTIAL_CONTENT)
            else:     # 扫码支付
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


class OrdersDetail(generics.GenericAPIView):
    queryset = Orders.objects.all()
    serializer_class = OrdersSerializer

    def get_object(self, *args, **kwargs):
        try:
            return Orders.objects.get(**kwargs)
        except Orders.DoesNotExist:
            raise status.HTTP_404_NOT_FOUND

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
        object_data = Orders.get_object_by_orders_id(**cld)
        if isinstance(object_data, Exception):
            return Response({'Detail': object_data.args}, status=status.HTTP_400_BAD_REQUEST)
        serializer = OrdersSerializer(object_data)
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
        return VerifyOrders.filter_consuming_orders_list(request, **cld)

    def get_finished_list(self, request, cld):
        business_orders = Orders.filter_finished_orders_list(request, **cld)
        verify_orders = VerifyOrders.filter_finished_orders_list(request, **cld)
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
        return VerifyOrders.filter_consuming_orders_list(request=request, **kwargs)

    def is_request_data_valid(self, request):
        form = VerifyOrdersListForm(request.data)
        if not form.is_valid():
            return False, Exception(form.errors)

        cld = form.cleaned_data
        result = ConfirmConsume.get_object(**cld)
        if isinstance(result, Exception):
            return False, result
        return True, result

    def post(self, request, *args, **kwargs):
        is_valid, instance = self.is_request_data_valid(request)
        if not is_valid:
            return Response({'Detail': instance.args}, status=status.HTTP_400_BAD_REQUEST)

        consumer_id = instance.user_id
        results = self.get_verify_orders_list(request, consumer_id)
        if isinstance(results, Exception):
            return Response({'Detail': results.args}, status=status.HTTP_400_BAD_REQUEST)

        serializer = VerifyOrdersListSerializer(data=results)
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
    def get_verify_orders_list(self, request, consumer_id):
        kwargs = {'consumer_id': consumer_id}
        return VerifyOrders.filter_consuming_orders_list(request=request, is_detail=False, **kwargs)

    def get_orders_detail(self, instances):
        return VerifyOrders.make_instances_to_dict(instances)

    def is_request_data_valid(self, request):
        form = VerifyOrdersActionForm(request.data)
        if not form.is_valid():
            return False, Exception(form.errors)

        cld = form.cleaned_data
        result = ConfirmConsume.get_object(**cld)
        if isinstance(result, Exception):
            return False, result
        return True, result

    def put(self, request, *args, **kwargs):
        is_valid, instance = self.is_request_data_valid(request)
        if not is_valid:
            return Response({'Detail': instance.args}, status=status.HTTP_400_BAD_REQUEST)

        consumer_id = instance.user_id
        results = self.get_verify_orders_list(request, consumer_id)
        if isinstance(results, Exception):
            return Response({'Detail': results.args}, status=status.HTTP_400_BAD_REQUEST)

        serializer = VerifySerializer()
        result_data = serializer.confirm_consume(results)
        if isinstance(result_data, Exception):
            return Response({'Detail': result_data.args}, status=status.HTTP_400_BAD_REQUEST)

        detail_list = self.get_orders_detail(result_data)
        serializer = VerifyOrdersListSerializer(data=detail_list)
        if not serializer.is_valid():
            return Response({'Detail': serializer.errors}, status=status.HTTP_206_PARTIAL_CONTENT)
        results = serializer.list_data()
        if isinstance(results, Exception):
            return Response({'Detail': results.args}, status=status.HTTP_400_BAD_REQUEST)
        return Response(results, status=status.HTTP_206_PARTIAL_CONTENT)


class SaleList(generics.GenericAPIView):
    queryset = Orders.objects.all()
    serializer_class = OrdersSerializer
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

        serializer = SaleListSerializer(data=object_data)
        if serializer.is_valid():
            results = serializer.list_data(**cld)
            if isinstance(results, Exception):
                return Response({'Detail': results.args}, status=status.HTTP_400_BAD_REQUEST)
            return Response(results, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
