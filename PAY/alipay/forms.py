# -*- encoding: utf-8 -*-
from django import forms


class PreCreateCallbackForm(forms.Form):
    app_id = forms.CharField(max_length=32, required=False)
    out_trade_no = forms.CharField(max_length=32)
    trade_status = forms.CharField(max_length=32)
    sign = forms.CharField(max_length=2048)

    seller_email = forms.EmailField(max_length=128, required=False)
    buyer_pay_amount = forms.CharField(max_length=16, required=False)
    point_amount = forms.CharField(max_length=16, required=False)
    subject = forms.CharField(max_length=256, required=False)
    open_id = forms.CharField(max_length=32, required=False)

    buyer_logon_id = forms.CharField(max_length=128, required=False)
    gmt_create = forms.CharField(max_length=20, required=False)

    invoice_amount = forms.CharField(max_length=16, required=False)
    sign_type = forms.CharField(max_length=10, required=False)

    fund_bill_list = forms.CharField(max_length=256, required=False)
    receipt_amount = forms.CharField(max_length=16, required=False)

    gmt_payment = forms.CharField(max_length=20, required=False)
    trade_no = forms.CharField(max_length=32, required=False)
    seller_id = forms.CharField(max_length=32, required=False)
    total_amount = forms.CharField(max_length=16, required=False)
    buyer_id = forms.CharField(max_length=32, required=False)

    charset = forms.CharField(max_length=12, required=False)
    version = forms.CharField(max_length=5, required=False)
    auth_app_id = forms.CharField(max_length=32, required=False)
    notify_time = forms.CharField(max_length=20, required=False)
    notify_id = forms.CharField(max_length=64, required=False)
    notify_type = forms.CharField(max_length=64, required=False)
