# -*- encoding: utf-8 -*-
from django import forms


class OrdersInputForm(forms.Form):
    dishes_ids = forms.CharField()


class OrdersGetForm(forms.Form):
    orders_id = forms.CharField(max_length=50)

