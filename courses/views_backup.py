from django.shortcuts import get_object_or_404
from rest_framework import viewsets, permissions, filters, status
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action
from rest_framework.response import Response

# Импорты моделей
from .models import Course, Lesson, Subscription
from users.models import Payment  # Payment из users

# Импорты сериализаторов
from .serializers import CourseSerializer, LessonSerializer, SubscriptionSerializer

# Импорты permissions
from .permissions import IsModerator, IsOwner

# Импорты пагинации
from .paginators import CoursePagination, LessonPagination, SubscriptionPagination

# Импорты для документации
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes


class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description']
    ordering_fields = ['created_at', 'title']
    pagination_class = CoursePagination

    def get_permissions(self):
        """
        Настраиваем права доступа в зависимости от действия
        """
        if self.action == 'create':
            permission_classes = [permissions.IsAuthenticated & ~IsModerator]
        elif self.action in ['update', 'partial_update']:
            permission_classes = [permissions.IsAuthenticated & (IsModerator | IsOwner)]
        elif self.action == 'destroy':
            permission_classes = [permissions.IsAuthenticated & IsOwner & ~IsModerator]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        """
        Модераторы и администраторы видят все курсы, обычные пользователи - только свои
        """
        user = self.request.user

        if not user.is_authenticated:
            return Course.objects.none()

        if user.is_superuser or user.groups.filter(name='moderators').exists():
            return Course.objects.all()

        return Course.objects.filter(owner=user)

    def perform_create(self, serializer):
        """
        Автоматически назначаем владельца при создании курса
        """
        serializer.save(owner=self.request.user)

    def get_serializer_context(self):
        """Добавляем request в контекст сериализатора"""
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def subscribe(self, request, pk=None):
        # ... ваш код ...
        return Response({...})

    @extend_schema(
        summary="Купить курс",
        description="Начинает процесс покупки курса через Stripe",
        request=None,
        responses={
            200: {
                'description': 'Ссылка для оплаты',
                'example': {
                    'url': 'https://checkout.stripe.com/pay/...',
                    'payment_id': 1,
                    'session_id': 'cs_test_...'
                }
            }
        }
    )
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def buy(self, request, pk=None):
        """
        Покупка курса - простой вызов StripePaymentViewSet
        """
        # ... ваш код ...
        return Response({...})

    # ДЕКОРАТОР @extend_schema_view ДОЛЖЕН БЫТЬ ПОСЛЕ ВСЕХ МЕТОДОВ, НО ВНУТРИ КЛАССА
    @extend_schema_view(
        list=extend_schema(
            summary="Получить список курсов",
            description="Возвращает список всех курсов с пагинацией (5 на страницу).",
            parameters=[
                OpenApiParameter(
                    name='page',
                    type=OpenApiTypes.INT,
                    location=OpenApiParameter.QUERY,
                    description='Номер страницы'
                ),
            ]
        ),
        retrieve=extend_schema(
            summary="Получить детали курса",
            description="Возвращает детальную информацию о курсе, включая поле is_subscribed."
        ),
        create=extend_schema(
            summary="Создать новый курс",
            description="Создает новый курс. Требуется авторизация."
        ),
        update=extend_schema(
            summary="Обновить курс",
            description="Полностью обновляет курс. Доступно владельцу или модератору."
        ),
        partial_update=extend_schema(
            summary="Частично обновить курс",
            description="Частично обновляет курс. Доступно владельцу или модератору."
        ),
        destroy=extend_schema(
            summary="Удалить курс",
            description="Удаляет курс. Доступно только владельцу."
        ),
    )


class LessonViewSet(viewsets.ModelViewSet):
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['course']
    search_fields = ['title', 'description']
    ordering_fields = ['created_at', 'title']
    pagination_class = LessonPagination

    def get_permissions(self):
        if self.action == 'create':
            permission_classes = [permissions.IsAuthenticated & ~IsModerator]
        elif self.action in ['update', 'partial_update']:
            permission_classes = [permissions.IsAuthenticated & (IsModerator | IsOwner)]
        elif self.action == 'destroy':
            permission_classes = [permissions.IsAuthenticated & IsOwner & ~IsModerator]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        user = self.request.user

        if not user.is_authenticated:
            return Lesson.objects.none()

        if user.is_superuser or user.groups.filter(name='moderators').exists():
            return Lesson.objects.all()

        return Lesson.objects.filter(owner=user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class SubscriptionViewSet(viewsets.ModelViewSet):
    """ViewSet для управления подписками пользователя"""
    queryset = Subscription.objects.all()
    serializer_class = SubscriptionSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = SubscriptionPagination

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

    def perform_create(self, serializer):
        course_id = self.request.data.get('course') or self.request.data.get('course_id')

        if not course_id:
            serializer.is_valid(raise_exception=True)
            return

        course = get_object_or_404(Course, id=course_id)
        serializer.save(user=self.request.user, course=course, is_active=True)

