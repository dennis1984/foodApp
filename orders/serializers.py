from orders.models import Orders
from rest_framework.serializers import ModelSerializer


class OrdersSerializer(ModelSerializer):
    class Meta:
        model = Orders
        fields = ("order_id", )
