from django.conf.urls import url, include
from rest_framework.routers import DefaultRouter
from orders.views import OrdersViewSet

router = DefaultRouter()  # 定义 router
router.register('orders', OrdersViewSet)  # 注册 viewset

urlpatterns = [
    url(r'^', include(router.urls)),  # 在 urlpatterns 里包含 router
]
