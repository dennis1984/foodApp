from dishes.models import Dishes
from rest_framework import serializers


class DishesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dishes
        fields = ('dishes_id', 'title', 'subtitle', 'description',
                  'price', 'image_url', 'user_id', 'extend')

    # pk = serializers.IntegerField(read_only=True)
    # order_id = serializers.CharField(max_length=50)
    # user_id = serializers.IntegerField(read_only=True)
    # city = serializers.CharField(max_length=200)
    # meal_center = serializers.CharField(max_length=300)
    # meal_ids = serializers.JSONField()
    # payable = serializers.CharField(max_length=50)
    # payment_status = serializers.IntegerField(default=0)
    # extend = serializers.JSONField(required=False)

    def create(self, dishes_data):
        return Dishes.objects.create(**dishes_data)

    def update(self, instance, dishes_data):
        instance.save()
        return instance

    # class Meta:
    #     model = Orders
    #     fields = ("order_id", )
