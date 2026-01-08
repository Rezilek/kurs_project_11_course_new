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
from drf_spectacular.utils import extend_schema
from drf_spectacular.types import OpenApiTypes


# НЕ импортируйте PaymentViewSet здесь!


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

    @extend_schema(
        summary="Подписаться или отписаться от курса",
        description="""Позволяет текущему пользователю подписаться на курс или отписаться от него.
        При первом вызове создается подписка. При повторном — отписывает пользователя (переключатель).""",
        responses={
            200: {'description': 'Статус подписки успешно изменен'},
            404: {'description': 'Курс не найден'},
        }
    )
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def subscribe(self, request, pk=None):
        """
        Подписаться или отписаться от курса.
        Если подписка существует - переключает её активность.
        Если не существует - создает активную подписку.
        """
        course = self.get_object()
        user = request.user

        subscription, created = Subscription.objects.get_or_create(
            user=user,
            course=course
        )

        if created:
            subscription.is_active = True
            message = "Вы успешно подписались на курс"
        else:
            subscription.is_active = not subscription.is_active
            message = "Вы отписались от курса" if not subscription.is_active else "Вы снова подписались на курс"

        subscription.save()

        return Response({
            'status': 'success',
            'message': message,
            'is_subscribed': subscription.is_active,
            'course_id': course.id,
            'course_title': course.title
        })

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def buy(self, request, pk=None):
        """Покупка курса"""
        course = self.get_object()

        # Проверяем цену курса
        if not hasattr(course, 'price') or course.price <= 0:
            return Response(
                {'error': 'Курс не имеет цены или цена равна 0'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Проверяем, не куплен ли уже курс
        # ВНИМАНИЕ: поле называется paid_course, а не course!
        existing_payment = Payment.objects.filter(
            user=request.user,
            paid_course=course,  # Исправлено: paid_course вместо course
            status='paid'
        ).exists()

        if existing_payment:
            return Response(
                {'error': 'Вы уже приобрели этот курс'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Создаем запись о платеже
        try:
            payment = Payment.objects.create(
                user=request.user,
                paid_course=course,  # Исправлено: paid_course вместо course
                amount=course.price,
                currency='rub',
                payment_method='stripe',
                status='pending'
            )

            return Response({
                'status': 'pending',
                'payment_id': payment.id,
                'course_id': course.id,
                'amount': float(payment.amount),
                'currency': payment.currency,
                'message': 'Платеж создан. Для завершения оплаты используйте PaymentViewSet.'
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({
                'error': f'Ошибка создания платежа: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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