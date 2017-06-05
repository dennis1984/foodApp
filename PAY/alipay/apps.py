from __future__ import unicode_literals

from django.apps import AppConfig


class AlipayConfig(AppConfig):
    name = 'PAY.alipay'

    def ready(self):
        self.module.autodiscover()
