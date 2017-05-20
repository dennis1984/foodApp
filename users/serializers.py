#-*- coding:utf8 -*-
from django.contrib.auth.models import User, Group
from django.contrib.auth.hashers import make_password
from rest_framework import serializers
from users.models import BusinessUser


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


class UserResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = BusinessUser
        fields = ('id', 'phone', 'business_name', 'food_court_id', 'last_login')


class GroupSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Group
        fields = ('url', 'name')

