# -*- encoding: utf-8 -*-
from django import forms


class OrdersInputForm(forms.Form):
    # username = forms.CharField(max_length = 128)
    # password = forms.CharField('', max_length = 128)

    city = forms.CharField(max_length=200)
    meal_center = forms.CharField(max_length=300)
    dishes_ids = forms.CharField()

