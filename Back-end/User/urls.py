# urls.py
from django.urls import path
from .views import *

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='custom_login'),
    path('owner/<int:owner_id>/', OwnerView.as_view(), name='owner_dashboard'),
    path('owner/<int:owner_id>/menu/', MenuView.as_view(), name='owner_menu'),
    path('owner/<int:owner_id>/workers/', WorkersView.as_view(), name='owner_workers'),





    path('waiter/<int:waiter_id>/', WaiterView.as_view(), name='waiter_dashboard'),
    path('chef/<int:chef_id>/', ChefView.as_view(), name='chef_dashboard'),



    # ========== API =========== #
    path('dashboard/chart-data/', DashboardChartData.as_view(), name='dashboard_chart_data'),

]
