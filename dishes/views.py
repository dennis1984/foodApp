# -*- coding: utf8 -*-
from rest_framework.renderers import JSONRenderer
from rest_framework.parsers import JSONParser
from rest_framework import status
from rest_framework.response import Response
from rest_framework import mixins
from rest_framework import generics

from dishes.models import Dishes
from dishes.serializers import DishesSerializer
from dishes.forms import DishesInputForm


class DishesList(mixins.CreateModelMixin, generics.GenericAPIView,
                 mixins.RetrieveModelMixin):
    queryset = Dishes.objects.all()
    serializer_class = DishesSerializer

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        """
        :param request: 
        :param args: 
        :param kwargs: {'title': '', 
                        'subtitle': '',
                        'description': '',
                        'price': '',
                        }
        :return: 
        """
        form = DishesInputForm(request.data)
        if not form.is_valid():
            return Response(request.data, status=status.HTTP_400_BAD_REQUEST)

        cld = form.cleaned_data
        serializer = DishesSerializer(data=cld)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

