"""
URL configuration for foodgram project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
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
from django.urls import include, path
from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.views.decorators.csrf import ensure_csrf_cookie
from users.views import UsersViewSet

@ensure_csrf_cookie
def get_csrf_token(request):
    return JsonResponse({'csrfToken': get_token(request)})

urlpatterns = [
    path('api/get-csrf-token/', get_csrf_token, name='get-csrf-token'),
    path('admin/', admin.site.urls),
    path('api/users/', include('users.urls')),  # Custom user routes
    path('api/auth/', include('djoser.urls.authtoken')),  # Только токены
    path('api/', include('recipes.urls')),
]