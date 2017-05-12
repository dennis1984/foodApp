# -*- coding: utf8 -*-
from rest_framework.renderers import JSONRenderer
from rest_framework.parsers import JSONParser
from dishes.models import Dishes
from dishes.serializers import DishesSerializer

from rest_framework import status
# from rest_framework.decorators import api_view, permission_classes
# from rest_framework import permissions
from rest_framework.response import Response

from rest_framework import mixins
from rest_framework import generics
# from dishes.forms import OrdersInputForm


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
        :param kwargs: {'city': '', 
                        'meal_center': '',
                        'dishes_ids': {'dishes_id': '',
                                       'count': '',
                                       },
                        }
        :return: 
        """
        form = OrdersInputForm(request.data)
        if not form.is_valid():
            return Response(request.data, status=status.HTTP_400_BAD_REQUEST)

        cld = form.cleaned_data
        dishes_ids = JSONRenderer().render(cld['dishes_ids'])

        return Response(dishes_ids)

        # return self.create(request, *args, **kwargs)



