from django.urls import path
from .views import *

urlpatterns = [
    # ====== Dysplay Pages ====== #

                # ====== Tables ====== #
        path('table/<str:token>/', TableView.as_view(), name='table'),


    # ========== "APIs" =========== #

                # ====== Tables ====== #
        path('table/<str:token>/authenticate/', AuthCodeView.as_view(), name='table_authenticate'),
        path('table/<str:token>/order/', OrderView.as_view(), name='table_order'),

                # ====== Menu ====== #
        path('<int:restaurant_id>/menu/categories/', CategoriesView.as_view(), name='categories_restaurant'),
        path('<int:restaurant_id>/menu/categories/<int:category_id>/elements/', CategoryElementsView.as_view(), name='category_elements_restaurant'),

                # ====== Orders ====== #
        path('<int:restaurant_id>/orders/pending/', PendingOrdersView.as_view(), name='orders_pending'),
        path('<int:restaurant_id>/orders/<int:pk>/complete/', CompleteOrderView.as_view(), name='order_complete'),
]