from django.urls import path
from .views import *

urlpatterns = [
        path('<int:restaurant_id>/orders/pending/', PendingOrdersView.as_view(), name='orders_pending'),
        path('<int:restaurant_id>/orders/<int:pk>/complete/', CompleteOrderView.as_view(), name='order_complete'),
]