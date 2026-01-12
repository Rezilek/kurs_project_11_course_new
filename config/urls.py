from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect
from django.http import JsonResponse
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView


def api_root(request):
    return JsonResponse({
        'message': 'API образовательной платформы',
        'endpoints': {
            'users': '/api/users/',
            'payments': '/api/users/payments/',
            'courses': '/api/courses/',
            'lessons': '/api/courses/lessons/',
            'subscriptions': '/api/courses/subscriptions/',
            'stripe_payments': '/api/courses/stripe-payments/',
        },
        'documentation': {
            'swagger': '/api/docs/',
            'redoc': '/api/redoc/',
            'schema': '/api/schema/'
        },
        'authentication': '/api/users/token/'
    })


def home_redirect(request):
    return redirect('/api/')


urlpatterns = [
    # 1. Админка
    path('admin/', admin.site.urls),

    # 2. Критически важно: Сначала ВСЕ другие маршруты с префиксом /api/
    path('api/users/', include('users.urls', namespace='users')),
    path('api/courses/', include('courses.urls')),

    # 3. Маршруты документации (тоже начинаются с /api/)
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    # 4. И только потом api_root для /api/ (без подпутей)
    path('api/', api_root, name='api-root'),

    # 5. Редирект с корня
    path('', home_redirect),
]

# Статические файлы в режиме отладки
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)