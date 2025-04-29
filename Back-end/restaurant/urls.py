from django.urls import path
from .views import *

urlpatterns = [
    
    path('api/create/restaurante/', CreateRestaurante.as_view(), name='create_restaurant'), 
    path('api/create/menu/', CreateMenu.as_view(), name='create_menu'), 
    path('api/create/category/', CreateCategory.as_view(), name='create_category'),
    path('api/create/category_element/', CreateCategoryElement.as_view(), name='create_element'), 



]