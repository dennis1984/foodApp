# -*- encoding: utf-8 -*-
from django import forms


class DishesInputForm(forms.Form):
    title = forms.CharField(max_length=200)
    subtitle = forms.CharField(max_length=200, required=False)
    description = forms.CharField(max_length=500, required=False)
    price = forms.CharField(max_length=50)

