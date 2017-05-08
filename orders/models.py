from __future__ import unicode_literals

from django.db import models


class Orders(models.Model):
    order_id = models.CharField(max_length=50, primary_key=True)
    user_id = models.IntegerField(db_index=True, null=False)
    city = models.CharField(max_length=200)
    food_city = models.CharField(max_length=300)
    food_ids = models.TextField()
    payable = models.CharField()
    created = models.DateTimeField(auto_created=True)
    updated = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'ys_orders'


