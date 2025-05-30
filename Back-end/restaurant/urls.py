from django.urls import path
from .views import *

urlpatterns = [
        
                # ====== Tables ====== #
        path('t/<str:token>/', TableView.as_view(), name='table'),


                # ====== Orders ====== #
        path('<int:restaurant_id>/orders/pending/', PendingOrdersView.as_view(), name='orders_pending'),
        path('<int:restaurant_id>/orders/<int:pk>/complete/', CompleteOrderView.as_view(), name='order_complete'),
]