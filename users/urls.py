from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import PaymentViewSet, UserViewSet
from .views import test_encoding


app_name = 'users'  # Добавляем app_name

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='users')
router.register(r'payments', PaymentViewSet, basename='payments')

urlpatterns = [
    path('', include(router.urls)),
    path('auth/', include('rest_framework.urls')),
    # JWT эндпоинты
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('test-encoding/', test_encoding, name='test-encoding'),
]
