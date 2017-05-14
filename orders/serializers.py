from orders.models import Orders
from rest_framework import serializers


class OrdersSerializer(serializers.ModelSerializer):

    class Meta:
        model = Orders
        # fields = ('id', 'order_id', 'user_id', 'city', 'meal_center',
        #           'meal_ids', 'payable', 'payment_status', 'extend')
        fields = '__all__'

    # pk = serializers.IntegerField(read_only=True)
    # order_id = serializers.CharField(max_length=50)
    # user_id = serializers.IntegerField(read_only=True)
    # city = serializers.CharField(max_length=200)
    # meal_center = serializers.CharField(max_length=300)
    # meal_ids = serializers.JSONField()
    # payable = serializers.CharField(max_length=50)
    # payment_status = serializers.IntegerField(default=0)
    # extend = serializers.JSONField(required=False)

    def create(self, orders_data):
        return Orders.objects.create(**orders_data)

    def update(self, instance, orders_data):
        instance.save()
        return instance

    # class Meta:
    #     model = Orders
    #     fields = ("order_id", )
