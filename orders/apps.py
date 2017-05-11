from __future__ import unicode_literals

from django.apps import AppConfig
from orders.models import Orders


class OrdersConfig(AppConfig):
    name = 'orders'

    def ready(self):
        MyModel = self.get_model('Orders')
