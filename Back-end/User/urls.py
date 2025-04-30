# urls.py
from django.urls import path
from .views import *

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('api/register/', ApiRegisterView.as_view(), name='api_register'),  

]
