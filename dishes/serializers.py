from dishes.models import Dishes
from rest_framework import serializers
import datetime


class DishesSerializer(serializers.ModelSerializer):
    def __init__(self, data, request, **kwargs):
        data['user_id'] = request.user.id
        super(DishesSerializer, self).__init__(data=data, **kwargs)

    class Meta:
        model = Dishes
        # fields = ('dishes_id', 'title', 'subtitle', 'description',
        #           'price', 'image_url', 'user_id', 'extend')
        fields = '__all__'

    # def create(self, dishes_data):
    #     return Dishes.objects.create(**dishes_data)
    #
    # def update(self, instance, dishes_data):
    #     instance.save()
    #     return instance


class DishesResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dishes
        fields = '__all__'

    @property
    def data(self):
        serializer = super(DishesResponseSerializer, self).data
        serializer['updated'] = timezoneStringTostring(serializer['updated'])
        serializer['created'] = timezoneStringTostring(serializer['created'])
        return serializer


def timezoneStringTostring(timezone_string):
    timezone = datetime.datetime.strptime(timezone_string, '%Y-%m-%dT%H:%M:%SZ')
    return str(timezone)
