from __future__ import unicode_literals

from django.apps import AppConfig


class WxpayConfig(AppConfig):
    name = 'PAY.wxpay'

    def ready(self):
        self.module.autodiscover()
