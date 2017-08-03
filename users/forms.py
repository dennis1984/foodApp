# -*- encoding: utf-8 -*-
# from django import forms
from horizon import forms


class UsersInputForm(forms.Form):
    username = forms.CharField(max_length=20, min_length=11,
                               error_messages={'required': u'手机号不能为空',
                                               'min_length': u'手机号位数不够'})
    password = forms.CharField(min_length=6, max_length=50,
                               error_messages={'required': u'密码不能为空',
                                               'min_length': u'密码长度不能少于6位'})
    identifying_code = forms.CharField(max_length=10, error_messages={'required': u'验证码不能为空'})
    business_name = forms.CharField(min_length=2, max_length=100)
    food_court_id = forms.IntegerField(min_value=1)


class ChangePasswordForm(forms.Form):
    password = forms.CharField(min_length=6,
                               max_length=50,
                               error_messages={
                                   'required': u'密码不能为空',
                                   'min_length': u'密码长度不能少于6位'
                               })


class UserListForm(forms.Form):
    start_created = forms.DateField(required=False)
    end_created = forms.DateField(required=False)
    page_size = forms.IntegerField(min_value=1, required=False)
    page_index = forms.IntegerField(min_value=1, required=False)


class SendIdentifyingCodeForm(forms.Form):
    username = forms.CharField(max_length=18)


class BusinessUserChangePasswordForm(ChangePasswordForm):
    identifying_code = forms.CharField(min_length=6, max_length=6)


class BusinessUserNoAuthResetPasswordForm(BusinessUserChangePasswordForm):
    username = forms.CharField(max_length=18)


class ClientInputForm(forms.Form):
    ip = forms.GenericIPAddressField()
    port = forms.IntegerField(min_value=1)
