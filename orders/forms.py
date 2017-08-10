# -*- encoding: utf-8 -*-
# from django import forms
from horizon import forms


class OrdersInputForm(forms.Form):
    dishes_ids = forms.CharField()


class OrdersGetForm(forms.Form):
    orders_id = forms.CharField(max_length=50)


class OrdersListForm(forms.Form):
    filter = forms.ChoiceField(choices=(('all', 1),
                                        ('pay', 2),
                                        ('consume', 3),
                                        ('finished', 4),
                                        ('expired', 5)),
                               required=False)
    start_created = forms.DateField(required=False)
    end_created = forms.DateField(required=False)
    payment_status = forms.IntegerField(required=False, max_value=500)
    page_size = forms.IntegerField(required=False)
    page_index = forms.IntegerField(required=False)


class OrdersUpdateForm(forms.Form):
    orders_id = forms.CharField(max_length=50)
    payment_status = forms.IntegerField(min_value=200, required=False)
    # payment_mode = forms.IntegerField(min_value=1, max_value=3)
    payment_mode = forms.ChoiceField(choices=(('cash', 1),
                                              ('scan', 2),
                                              ('yinshi', 3)),
                                     error_messages={
                                         'required': 'Field [payment_mode] must in '
                                                     '["cash", "scan", "yinshi"]'
                                     })


class VerifyOrdersListForm(forms.Form):
    random_string = forms.CharField(max_length=32)
    gateway = forms.ChoiceField(choices=(('yinshi_pay', 1),
                                         ('confirm_consume', 2)),
                                required=False)


class VerifyOrdersActionForm(forms.Form):
    # 数据结构
    # orders_ids = "['Z201707080001', 'Z201707080002', ...]"
    orders_ids = forms.CharField()
    random_string = forms.CharField(max_length=32)


class SaleListForm(forms.Form):
    # user_id = forms.IntegerField(required=False)
    start_created = forms.DateField(required=False)
    end_created = forms.DateField(required=False)
    # payment_mode = forms.IntegerField(required=False, min_value=1, max_value=3)
    page_size = forms.IntegerField(min_value=1, required=False)
    page_index = forms.IntegerField(min_value=1, required=False)
