# -*- coding:utf8 -*-
from django.conf.urls import url, include
from rest_framework.urlpatterns import format_suffix_patterns
from wallet import views

urlpatterns = [
    url(r'^wallet_action/$', views.WalletAction.as_view()),
    url(r'^wallet_detail/$', views.WalletDetail.as_view()),
    url(r'^wallet_trade_list/$', views.WalletTradeDetailList.as_view()),

    url(r'^withdraw_action/$', views.WithdrawAction.as_view()),
    url(r'^withdraw_record_list/$', views.WithdrawRecordList.as_view()),

    url(r'^bank_card_action/$', views.BankCardAction.as_view()),
    url(r'^bank_card_list/$', views.BankCardList.as_view()),
]

urlpatterns = format_suffix_patterns(urlpatterns)


