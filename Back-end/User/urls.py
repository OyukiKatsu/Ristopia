# urls.py
from django.urls import path
from .views import *

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='custom_login'),
    path('reset-password/', ResetPasswordView.as_view(), name='reset_password'),
    path('reset-password/<uidb64>/<token>/', ResetPasswordTokenView.as_view(), name='custom_password_reset_confirm'),
    path('owner/<int:owner_id>/', OwnerView.as_view(), name='owner_dashboard'),
    path('owner/<int:owner_id>/menu/', MenuView.as_view(), name='owner_menu'),
    path('owner/<int:owner_id>/workers/', WorkersView.as_view(), name='owner_workers'),





    path('waiter/<int:waiter_id>/', WaiterView.as_view(), name='waiter_dashboard'),
    path('chef/<int:chef_id>/', ChefView.as_view(), name='chef_dashboard'),



    # ========== API =========== #
    path('reset-password/api', ResetPasswordEmailView.as_view(), name='api_password_reset'),
    path('dashboard/chart-data/', DashboardChartData.as_view(), name='dashboard_chart_data'),
    path('owner/<int:owner_id>/menu/create/', CreateMenuView.as_view(), name='create_menu'),
    path('owner/<int:owner_id>/menu/category/add/', CreateCategoryView.as_view(), name='create_category'),
    path('owner/<int:owner_id>/menu/category-element/add/', CreateCategoryElementView.as_view(), name='create_category_element'),
    path("owner/<int:owner_id>/menu/category/<int:pk>/toggle/", ToggleCategoryActiveView.as_view(), name="toggle_category_active"),
    path("owner/<int:owner_id>/menu/category/<int:pk>/update/", UpdateCategoryView.as_view(), name="update_category"),
    path("owner/<int:owner_id>/menu/category/<int:pk>/delete/", DeleteCategoryView.as_view(), name="delete_category"),

    path("owner/<int:owner_id>/menu/category-element/<int:pk>/toggle/", ToggleCategoryElementActiveView.as_view(), name="toggle_category_element_active"),
    path("owner/<int:owner_id>/menu/category-element/<int:pk>/update/", UpdateCategoryElementView.as_view(), name="update_category_element"),
    path("owner/<int:owner_id>/menu/category-element/<int:pk>/delete/", DeleteCategoryElementView.as_view(), name="delete_category_element"),


    path('owner/<int:owner_id>/menu/category/<int:category_id>/elements/', CategoryElementsView.as_view(), name='get_category_elements'),
    path('owner/<int:owner_id>/workers/create/', CreateWorkerView.as_view(), name='create_worker'),
]
