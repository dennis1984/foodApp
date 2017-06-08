# -*- coding:utf8 -*-
from __future__ import unicode_literals

from django.db import models
from django.utils.timezone import now


class AliPayResult(models.Model):
    """
    微信支付结果信息
    """
    orders_id = models.CharField('订单ID', max_length=32, db_index=True, unique=True)

    trade_status = models.CharField('交易状态', max_length=32, null=True)
    app_id = models.CharField('支付宝分配给开发者的应用Id', max_length=32, null=True)
    subject = models.CharField('订单主题', max_length=256, null=True)
    trade_no = models.CharField('支付宝交易号', max_length=128, null=True)
    out_trade_no = models.CharField('商户订单号', max_length=32, null=True)
    total_amount = models.CharField('订单金额', max_length=16, null=True)
    receipt_amount = models.CharField('商家在交易中实际收到的款项（单位为元）', max_length=16, null=True)

    out_biz_no = models.CharField('商户业务号', max_length=32, null=True)
    body = models.CharField('商品描述', max_length=128, null=True)

    open_id = models.CharField('买家支付宝用户号', max_length=32, null=True)
    buyer_logon_id = models.CharField('买家支付宝账号', max_length=32, null=True)
    buyer_id = models.CharField('买家的支付宝用户Uid', max_length=32, null=True)
    seller_id = models.CharField('卖家支付宝用户号', max_length=32, null=True)
    seller_email = models.CharField('卖家支付宝账号', max_length=32, null=True)
    gmt_create = models.CharField('交易创建时间', max_length=32, null=True)
    gmt_payment = models.CharField('交易付款时间', max_length=32, null=True)
    gmt_refund = models.CharField('交易退款时间', max_length=32, null=True)
    gmt_close = models.CharField('交易结束时间', max_length=32, null=True)

    invoice_amount = models.CharField('用户在交易中支付的可开具发票的金额', max_length=16, null=True)
    buyer_pay_amount = models.CharField('用户在交易中支付的金额', max_length=16, null=True)
    point_amount = models.CharField('使用积分宝支付的金额', max_length=16, null=True)

    refund_fee = models.CharField('退款金额', max_length=16, null=True)
    fund_bill_list = models.CharField('支付金额信息', max_length=128, null=True)
    voucher_detail_list = models.CharField('本交易支付时所使用的所有优惠券信息', max_length=128, null=True)

    request_data = models.TextField('调用支付宝支付时传过去的数据（数据格式：json类型的dict）')
    created = models.DateTimeField('记录创建时间', default=now)
    extend = models.TextField('扩展信息', null=True)

    class Meta:
        db_table = 'ys_alipay'

    def __unicode__(self):
        return self.orders_id

    @classmethod
    def get_object_by_orders_id(cls, orders_id):
        try:
            return cls.objects.get(orders_id=orders_id)
        except cls.DoesNotExist as e:
            return Exception(e)

