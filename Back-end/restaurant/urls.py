from django.urls import path
from .views import *

urlpatterns = [
    
    path('api/create/', CreateRestaurante.as_view(), name='api_create_restaurant'), 
    path('api/create/menu/', CreateMenu.as_view(), name='api_create_menu'), 
    path('api/create/category/', CreateCategory.as_view(), name='api_create_category'),
    path('api/create/category_element/', CreateCategoryElement.as_view(), name='api_create_element'), 



]