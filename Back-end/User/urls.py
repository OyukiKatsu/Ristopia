# urls.py
from django.urls import path
from .views import *

urlpatterns = [

    path('api/register/', RegisterView.as_view(), name='register'),  

]
