# -*- encoding: utf-8 -*-
from django import forms


class OrdersInputForm(forms.Form):
    dishes_ids = forms.CharField()


class OrdersGetForm(forms.Form):
    orders_id = forms.CharField(max_length=50)


class OrdersListForm(forms.Form):
    start_created = forms.DateField(required=False)
    end_created = forms.DateField(required=False)
    page_size = forms.IntegerField(required=False)
    page_index = forms.IntegerField(required=False)


class OrdersUpdateForm(forms.Form):
    orders_id = forms.CharField(max_length=50)
    payment_status = forms.CharField(max_length=50)

