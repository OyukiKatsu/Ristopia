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
        path('table/<token>/orders/', TableOrdersView.as_view(), name='table_orders'),
        path('table/<token>/call_waiter/', TableCallWaiterView.as_view(), name='table_call_waiter'),
        path('table/<str:token>/is_open/', TableIsOpenView.as_view(), name='table_is_open'),



                # ====== Menu ====== #
        path('<int:restaurant_id>/menu/categories/', CategoriesView.as_view(), name='categories_restaurant'),
        path('<int:restaurant_id>/menu/categories/<int:category_id>/elements/', CategoryElementsView.as_view(), name='category_elements_restaurant'),


                # ====== Workers ====== #
        path('<int:restaurant_id>/maps/', MapsListView.as_view(), name='maps_list'),
        path('<int:restaurant_id>/maps/<int:map_id>/tables/', TablesOnMapView.as_view(), name='tables_on_map'),
        
                                # ====== Chef ====== #
                        path('<int:restaurant_id>/maps/<int:map_id>/tables/<int:table_id>/orders/', TableOrdersViewChef.as_view(), name='table_orders_for_chef'),
                        path('<int:restaurant_id>/orders/pending/', PendingCookingOrdersView.as_view(), name='orders_pending_chef'),
                        path('<int:restaurant_id>/orders/<int:pk>/complete/', CompleteOrderView.as_view(), name='order_complete'),
                        
                                # ====== Waiter ====== #
                        path('<int:restaurant_id>/maps/<int:map_id>/detail/', MapDetailView.as_view(), name='map_detail'),
                        path('<int:restaurant_id>/maps/<int:map_id>/tables/<int:table_id>/orders_waiter/',TableOrdersViewWaiter.as_view(), name='table_orders_for_waiter'),
                        path('<int:restaurant_id>/orders/to_deliver/', ToDeliverOrdersView.as_view(), name='orders_to_deliver'),
                        path('<int:restaurant_id>/orders/<int:pk>/delivered', DeliveredOrdersView.as_view(), name='order_delivered'),
                        path('<restaurant_id>/orders/<table_id>/update_comanda/', UpdateComandaView.as_view(), name='update_comanda'),
                        path('<int:restaurant_id>/table/<int:table_id>/open/',TableOpenView.as_view(),name='table_open'),
                        path('<int:restaurant_id>/table/<int:table_id>/close/',TableCloseView.as_view(),name='table_close'),
                        path('<int:restaurant_id>/table/<int:table_id>/attended/',TableAttendedView.as_view(),name='table_attended'),
]