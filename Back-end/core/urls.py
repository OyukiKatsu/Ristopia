# urls.py
from django.urls import path
from .views import ProfileListView  # Import the ProfileListView
from .views import Index
urlpatterns = [    
    path('', Index, name='index'),
]
