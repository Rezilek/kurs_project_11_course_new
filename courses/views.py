from django.shortcuts import get_object_or_404
from rest_framework import viewsets, permissions, filters, status, generics
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from datetime import timedelta
from .tasks import send_course_update_email
from .models import Course, Lesson, Subscription
from users.models import Payment
from .serializers import CourseSerializer, LessonSerializer, SubscriptionSerializer
from .permissions import IsModerator, IsOwner
from .paginators import CoursePagination, LessonPagination, SubscriptionPagination
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
            return Course.objects.none()
        if user.is_superuser or user.groups.filter(name='moderators').exists():
            return Course.objects.all()
        return Course.objects.filter(owner=user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    def get_serializer_context(self):
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

    @extend_schema(
        summary="Начать покупку курса",
        description="Создает платежную сессию для покупки курса через Stripe",
        responses={
            201: {'description': 'Перенаправление на страницу оплаты'},
            400: {'description': 'Ошибка валидации'},
            409: {'description': 'Курс уже куплен'}
        }
    )
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def buy(self, request, pk=None):
        from django.urls import reverse
        course = self.get_object()
        from users.models import Payment
        existing_payment = Payment.objects.filter(
            user=request.user,
            paid_course=course,
            status='paid'
        ).exists()
        if existing_payment:
            return Response(
                {'error': 'Вы уже приобрели этот курс'},
                status=status.HTTP_409_CONFLICT
            )
        payment_data = {
            'item_type': 'course',
            'item_id': course.id
        }
        return Response({
            'message': 'Для оплаты перейдите по ссылке',
            'payment_url': request.build_absolute_uri(
                reverse('users:payment-buy')
            ),
            'payment_data': payment_data,
            'course_id': course.id,
            'course_title': course.title,
            'course_price': float(course.price) if hasattr(course, 'price') else 0.0
        }, status=status.HTTP_200_OK)


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
        elif self.action in ['update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return Lesson.objects.none()
        if user.is_superuser:
            return Lesson.objects.all()
        if user.groups.filter(name='moderators').exists():
            return Lesson.objects.all()
        return Lesson.objects.filter(owner=user)

    def perform_create(self, serializer):
        lesson = serializer.save(owner=self.request.user)
        if lesson.course:
            lesson.course.updated_at = timezone.now()
            lesson.course.save()
        return lesson

    def perform_update(self, serializer):
        """
        При обновлении урока:
        1. Проверяем, прошло ли более 4 часов с последнего обновления курса
        2. Если да - отправляем асинхронные уведомления подписчикам
        3. Обновляем время курса
        """
        from .tasks import send_course_update_email

        lesson = self.get_object()
        course = lesson.course

        if not course:
            return serializer.save()

        # Сохраняем старое время курса
        last_updated = course.updated_at

        # Сохраняем обновленный урок
        updated_lesson = serializer.save()

        # Проверяем условие ДО обновления времени курса
        now = timezone.now()
        time_difference = now - last_updated if last_updated else timedelta(hours=5)

        # Проверка 4-х часов (дополнительное задание)
        if time_difference > timedelta(hours=4):
            update_message = f"Урок '{lesson.title}' был обновлен."
            # Асинхронная отправка уведомлений подписчикам
            send_course_update_email.delay(course.id, update_message)

        # Обновляем время курса ПОСЛЕ проверки
        course.updated_at = now
        course.save()

        return updated_lesson


class SubscriptionViewSet(viewsets.ModelViewSet):
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


class CourseUpdateAPIView(generics.UpdateAPIView):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = [permissions.IsAdminUser]

    def perform_update(self, serializer):
        course = self.get_object()
        last_updated = course.updated_at
        updated_course = serializer.save()
        now = timezone.now()
        time_difference = now - last_updated if last_updated else timedelta(hours=5)
        if time_difference > timedelta(hours=4):
            update_message = "Материалы курса были обновлены."
            send_course_update_email.delay(course.id, update_message)
        return updated_course


class LessonUpdateAPIView(generics.UpdateAPIView):
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    permission_classes = [permissions.IsAdminUser]

    def perform_update(self, serializer):
        lesson = self.get_object()
        course = lesson.course
        last_updated = course.updated_at
        updated_lesson = serializer.save()
        course.updated_at = timezone.now()
        course.save()
        now = timezone.now()
        time_difference = now - last_updated if last_updated else timedelta(hours=5)
        if time_difference > timedelta(hours=4):
            update_message = f"Урок '{lesson.title}' был обновлен."
            send_course_update_email.delay(course.id, update_message)
        return updated_lesson