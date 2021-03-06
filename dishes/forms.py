# -*- encoding: utf-8 -*-
from django.conf import settings
from horizon import forms


class DishesInputForm(forms.Form):
    title = forms.CharField(max_length=200)
    subtitle = forms.CharField(max_length=200, required=False)
    description = forms.CharField(max_length=500, required=False)
    price = forms.CharField(max_length=16)
    size = forms.IntegerField(min_value=10, max_value=20, required=False)
    size_detail = forms.CharField(min_length=2, max_length=30, required=False)
    image = forms.ImageField(required=False)
    classify = forms.IntegerField(min_value=1, required=False)
    extend = forms.CharField(max_length=500, required=False)


class DishesUpdateForm(forms.Form):
    title = forms.CharField(max_length=200, required=False)
    pk = forms.IntegerField(min_value=1)
    subtitle = forms.CharField(max_length=200, required=False)
    description = forms.CharField(max_length=500, required=False)
    price = forms.CharField(max_length=50, required=False)
    size = forms.IntegerField(min_value=10, max_value=20, required=False)
    size_detail = forms.CharField(min_length=2, max_length=30, required=False)
    image = forms.ImageField(required=False)
    is_recommend = forms.IntegerField(min_value=0, max_value=1, required=False)
    classify = forms.IntegerField(min_value=1, required=False)
    extend = forms.CharField(max_length=500, required=False)


class DishesDeleteForm(forms.Form):
    pk = forms.IntegerField(min_value=1)


class DishesListForm(forms.Form):
    gateway = forms.ChoiceField(choices=(('main_page', 1),
                                         ('edit_page', 2)),
                                required=False)
    classify = forms.IntegerField(min_value=1, required=False)
    page_size = forms.IntegerField(min_value=1, max_value=settings.MAX_PAGE_SIZE, required=False)
    page_index = forms.IntegerField(min_value=1, required=False)


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
    mall = forms.CharField(min_length=2, max_length=200, required=False)
    page_size = forms.IntegerField(min_value=1, max_value=settings.MAX_PAGE_SIZE, required=False)
    page_index = forms.IntegerField(min_value=1, required=False)


class DishesClassifyInputForm(forms.Form):
    name = forms.CharField(min_length=1, max_length=64)
    description = forms.CharField(min_length=1, max_length=256, required=False)


class DishesClassifyUpdateForm(forms.Form):
    id = forms.IntegerField(min_value=1)
    name = forms.CharField(min_length=1, max_length=64, required=False)
    description = forms.CharField(min_length=1, max_length=256, required=False)


class DishesClassifyDeleteForm(forms.Form):
    id = forms.IntegerField(min_value=1)


class DishesClassifyListForm(forms.Form):
    page_size = forms.IntegerField(min_value=1, required=False)
    page_index = forms.IntegerField(min_value=1, required=False)
