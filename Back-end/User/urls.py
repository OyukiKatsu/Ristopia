# urls.py
from django.urls import path
from .views import *

urlpatterns = [
    # ====== Dysplay Pages ====== #

        # ====== User Control ====== #
        path('register/', RegisterView.as_view(), name='register'),
        path('login/', LoginView.as_view(), name='custom_login'),
        path('reset-password/', ResetPasswordView.as_view(), name='reset_password'),
        path('reset-password/<uidb64>/<token>/', ResetPasswordTokenView.as_view(), name='custom_password_reset_confirm'),

        # ====== Owner Dashboards ====== #
        path('owner/<int:owner_id>/', OwnerView.as_view(), name='owner_dashboard'),

                # === Menu ==== #
            path('owner/<int:owner_id>/menu/', MenuView.as_view(), name='owner_menu'),

                # === Worker ==== #
            path('owner/<int:owner_id>/workers/', WorkersView.as_view(), name='owner_workers'),

                # === Map Creator ==== #
            path('owner/<int:owner_id>/map-creator/', MapCreatorView.as_view(), name='owner_map_creator'),


        # ====== Worker Dashboards ====== #

                # === Waiter ==== #
            path('waiter/<int:waiter_id>/', WaiterView.as_view(), name='waiter_dashboard'),

                # === Chef ==== #
            path('chef/<int:chef_id>/', ChefView.as_view(), name='chef_dashboard'),



    # ========== "APIs" =========== #

        # ====== User Control ====== #
        path('reset-password/api', ResetPasswordEmailView.as_view(), name='api_password_reset'),

        # ====== Owner Dashboards ====== #
        path('dashboard/chart-data/', DashboardChartData.as_view(), name='dashboard_chart_data'),

                # === Menu ==== #
            path('owner/<int:owner_id>/menu/create/', CreateMenuView.as_view(), name='create_menu'),

                # === Category ==== #
            path('owner/<int:owner_id>/menu/category/add/', CreateCategoryView.as_view(), name='create_category'),
            path("owner/<int:owner_id>/menu/category/<int:pk>/toggle/", ToggleCategoryActiveView.as_view(), name="toggle_category_active"),
            path("owner/<int:owner_id>/menu/category/<int:pk>/update/", UpdateCategoryView.as_view(), name="update_category"),
            path("owner/<int:owner_id>/menu/category/<int:pk>/delete/", DeleteCategoryView.as_view(), name="delete_category"),
            path('owner/<int:owner_id>/menu/category/<int:category_id>/elements/', CategoryElementsView.as_view(), name='get_category_elements'),

                # === Category Element ==== #
            path('owner/<int:owner_id>/menu/category-element/add/', CreateCategoryElementView.as_view(), name='create_category_element'),
            path("owner/<int:owner_id>/menu/category-element/<int:pk>/toggle/", ToggleCategoryElementActiveView.as_view(), name="toggle_category_element_active"),
            path("owner/<int:owner_id>/menu/category-element/<int:pk>/update/", UpdateCategoryElementView.as_view(), name="update_category_element"),
            path("owner/<int:owner_id>/menu/category-element/<int:pk>/delete/", DeleteCategoryElementView.as_view(), name="delete_category_element"),

                # === Worker ==== #
            path('owner/<int:owner_id>/workers/create/', CreateWorkerView.as_view(), name='create_worker'),
            path('owner/<int:owner_id>/workers/<int:worker_id>/toggle/', ToggleWorkerActiveView.as_view(), name='toggle_worker_active'),
            path('owner/<int:owner_id>/workers/<int:worker_id>/delete/', DeleteWorkerView.as_view(), name='delete_worker'),
                
                # === Map Creator ==== #
            path('owner/<int:owner_id>/map-creator/save', SaveMapView.as_view(), name='save_map'),
            path('owner/<int:owner_id>/map-creator/floor/create', CreateFloorView.as_view(), name='create_floor'),
            path('owner/<int:owner_id>/map-creator/qr', GenerateQR.as_view(), name='generate_qr'),

]
