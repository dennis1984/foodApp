#-*- coding:utf8 -*-
from django.contrib.auth.models import User, Group
from django.contrib.auth.hashers import make_password
from rest_framework import serializers
from users.models import BusinessUser
from horizon.main import timezoneStringTostring


# class UserSerializer(serializers.HyperlinkedModelSerializer):
#     class Meta:
#         model = User
#         fields = ('url', 'username', 'email', 'groups')
#         # fields = '__all__'

class UserSerializer(serializers.ModelSerializer):
    # dishes = serializers.PrimaryKeyRelatedField(many=True, queryset=Dishes.active_objects.all())

    class Meta:
        model = BusinessUser
        # fields = ('id', 'username', 'dishes')
        fields = '__all__'
        write_only_fields = ('password', )

    def update_password(self, instance, validated_data):
        password = validated_data.get('password', None)
        if password is None:
            raise ValueError('Password is cannot be empty.')
        validated_data['password'] = make_password(password)
        return super(UserSerializer, self).update(instance, validated_data)


class UserResponseSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    phone = serializers.CharField(max_length=20)
    business_name = serializers.CharField(max_length=100)
    food_court_id = serializers.IntegerField()
    last_login = serializers.DateTimeField()

    head_picture = serializers.ImageField()
    food_court_name = serializers.CharField(max_length=200)
    city = serializers.CharField(max_length=100)
    district = serializers.CharField(max_length=100)
    mall = serializers.CharField(max_length=200, required=False)

    @property
    def data(self):
        _data = super(UserResponseSerializer, self).data
        if _data.get('user_id', None):
            _data['last_login'] = timezoneStringTostring(_data['last_login'])
            _data['head_picture_url'] = _data['head_picture']
        return _data


# class UserResponseSerializer(serializers.ModelSerializer):
#     food_court_name = serializers.CharField(max_length=200)
#     city = serializers.CharField(max_length=100)
#     district = serializers.CharField(max_length=100)
#     mall = serializers.CharField(max_length=200)
#
#     class Meta:
#         model = BusinessUser
#         fields = ('id', 'phone', 'business_name', 'food_court_id', 'last_login',
#                   'head_picture', 'food_court_name', 'city', 'district', 'mall')


class GroupSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Group
        fields = ('url', 'name')

