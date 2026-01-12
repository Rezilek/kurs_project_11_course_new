# users/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

# Важно: импортируйте функции из views.py
from .views import (
    UserViewSet, PaymentViewSet,
    payment_success, payment_cancel,  # ← эти функции
    stripe_webhook, test_encoding
)

app_name = 'users'

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'payments', PaymentViewSet, basename='payment')

urlpatterns = [
    # 🔥 ПЕРВЫМИ должны идти эти маршруты:
    path('payments/success/', payment_success, name='payment-success'),
    path('payments/cancel/', payment_cancel, name='payment-cancel'),

    # Другие маршруты
    path('payments/webhook/', stripe_webhook, name='stripe-webhook'),
    path('payments/test-encoding/', test_encoding, name='test-encoding'),

    # JWT
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # ViewSet в конце
    path('', include(router.urls)),
]