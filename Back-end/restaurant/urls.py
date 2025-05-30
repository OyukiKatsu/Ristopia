from django.urls import path
from .views import *

urlpatterns = [
        
                # ====== Tables ====== #
        path('table/<str:token>/', TableView.as_view(), name='table'),


                # ====== Orders ====== #
        path('<int:restaurant_id>/orders/pending/', PendingOrdersView.as_view(), name='orders_pending'),
        path('<int:restaurant_id>/orders/<int:pk>/complete/', CompleteOrderView.as_view(), name='order_complete'),





        path('table/<str:token>/authenticate/', AuthCodeView.as_view(), name='table_authenticate'),


        path('<int:restaurant_id>/menu/categories/', CategoriesView.as_view(), name='categories_restaurant'),
        path('<int:restaurant_id>/menu/categories/<int:category_id>/elements/', CategoryElementsView.as_view(), name='category_elements_restaurant'),
]