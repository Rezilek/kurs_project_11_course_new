"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
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
from django.shortcuts import redirect
from django.http import JsonResponse
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

#urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


def redirect_to_api(request):
    return redirect('/api/')

def api_root(request):
    return JsonResponse({
        'message': 'API образовательной платформы',
        'endpoints': {
            'users': '/api/users/',
            'payments': '/api/users/payments/',
            'courses': '/api/courses/',
        },
        'filters': {
            'payments': {
                'by_course': '/api/users/payments/?paid_course=1',
                'by_lesson': '/api/users/payments/?paid_lesson=1',
                'by_method': '/api/users/payments/?payment_method=transfer',
                'sorted': '/api/users/payments/?ordering=-payment_date',
            }
        }
    })

def home_redirect(request):
    return redirect('/api/')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/users/', include(('users.urls', 'users'), namespace='users')),
    path('api/courses/', include('courses.urls')),
    path('api/', api_root, name='api-root'),  # ← Добавьте эту строку
    path('', home_redirect),
    # Маршруты для документации
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    # Swagger UI
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    # ReDoc
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)