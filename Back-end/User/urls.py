# urls.py
from django.urls import path
from .views import *

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('owner/<int:owner_id>/', OwnerView.as_view(), name='owner_dashboard'),
    path('waiter/<int:waiter_id>/', WaiterView.as_view(), name='waiter_dashboard'),
    path('chef/<int:chef_id>/', ChefView.as_view(), name='chef_dashboard'),
]
