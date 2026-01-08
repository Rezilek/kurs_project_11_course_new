from rest_framework import viewsets, permissions, status, serializers
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter
from drf_spectacular.utils import extend_schema
from drf_spectacular.types import OpenApiTypes

from .models import Payment
from .serializers import UserSerializer, UserRegisterSerializer, PaymentSerializer
from .permissions import IsOwner, IsModerator

User = get_user_model()


class UserSerialize:
    pass


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_serializer_class(self):
        if self.action == 'create':
            return UserRegisterSerializer
        return UserSerializer

    def get_permissions(self):
        """
        Настраиваем права доступа
        """
        if self.action == 'create':
            # Регистрация доступна всем
            permission_classes = [permissions.AllowAny]
        elif self.action in ['update', 'partial_update', 'destroy']:
            # Изменять и удалять можно только свой профиль
            permission_classes = [permissions.IsAuthenticated, IsOwner]
        else:
            # Просматривать профили могут все авторизованные
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]


    @action(detail=False, methods=['get', 'put', 'patch'])
    def me(self, request):
        """
        Получение и обновление профиля текущего пользователя
        """
        if request.method == 'GET':
            serializer = self.get_serializer(request.user)
            return Response(serializer.data)
        elif request.method in ['PUT', 'PATCH']:
            serializer = self.get_serializer(
                request.user,
                data=request.data,
                partial=(request.method == 'PATCH')
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)
        return None


class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['paid_course', 'paid_lesson', 'payment_method']
    ordering_fields = ['payment_date']

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]


# Создаем сериализатор для тестового эндпоинта
class TestEncodingResponseSerializer(serializers.Serializer):
    message = serializers.CharField()
    data = serializers.DictField()
    status = serializers.CharField()
    test = serializers.CharField()


@extend_schema(
    summary="Тестовый эндпоинт для проверки кодировки",
    description="Проверяет корректность работы UTF-8 кодировки в API",
    responses=TestEncodingResponseSerializer,
    tags=['Тестирование']
)
@api_view(['GET'])
@permission_classes([AllowAny])
def test_encoding(request):
    """Тестовый эндпоинт для проверки кодировки"""
    return Response({
        "message": "Тест русских символов",
        "data": {
            "city": "Москва",
            "name": "Иван Петров",
            "description": "Тестирование кодировки UTF-8 в Django DRF"
        },
        "status": "success",
        "test": "Привет мир! Санкт-Петербург, Казань, Екатеринбург"
    })