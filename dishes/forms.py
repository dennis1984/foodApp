# -*- encoding: utf-8 -*-
from django import forms


class DishesInputForm(forms.Form):
    title = forms.CharField(max_length=200)
    subtitle = forms.CharField(max_length=200, required=False)
    description = forms.CharField(max_length=500, required=False)
    price = forms.CharField(max_length=50)
    image = forms.ImageField(required=False)
    extend = forms.CharField(max_length=500, required=False)


class DishesUpdateForm(forms.Form):
    # title = forms.CharField(max_length=200, required=False)
    pk = forms.IntegerField(min_value=1)
    subtitle = forms.CharField(max_length=200, required=False)
    description = forms.CharField(max_length=500, required=False)
    price = forms.CharField(max_length=50, required=False)
    image = forms.ImageField(required=False)
    extend = forms.CharField(max_length=500, required=False)


class DishesDeleteForm(forms.Form):
    pk = forms.IntegerField(min_value=1)


class DishesGetForm(forms.Form):
    pk = forms.IntegerField(required=False)
    user_id = forms.IntegerField(required=False)
    title = forms.CharField(max_length=200, required=False)
    price = forms.CharField(max_length=50, required=False)


class FoodCourtGetForm(forms.Form):
    pk = forms.IntegerField(required=False)
    name = forms.CharField(max_length=200, required=False)


class FoodCourtListForm(forms.Form):
    city = forms.CharField(min_length=2, max_length=100, required=False)
    district = forms.CharField(min_length=2, max_length=100, required=False)



