"""
URL configuration for TFG project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from core.views import error_403, error_404, error_400

handler403 = error_403
handler404 = error_404
handler400 = error_400

urlpatterns = [
    path('', include('core.urls')),
    path('admin/', admin.site.urls), # Only for development
    path('user/', include('User.urls')), # All owner and worker urls
    path('restaurant/', include(('restaurant.urls', 'restaurant'), namespace='restaurant')), # All restaurant needed urls
    path('auth/', include('django.contrib.auth.urls')), # For logout
    
]   + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

