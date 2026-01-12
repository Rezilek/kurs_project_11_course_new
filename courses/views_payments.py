from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.urls import reverse
from drf_spectacular.utils import extend_schema, OpenApiParameter

from .models import Course, Lesson
from users.models import Payment
from .serializers import PaymentCreateSerializer, PaymentSerializer
from .services.stripe_service import StripeService

try:
    from users.models import Payment
except ImportError:
    from .models import Payment

class StripePaymentViewSet(viewsets.GenericViewSet):
    """
    ViewSet для обработки платежей через Stripe
    """
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Создать платеж через Stripe",
        description="""
        Создает платеж и сессию оплаты в Stripe.
        Возвращает ссылку для перенаправления на страницу оплаты.
        """,
        request=PaymentCreateSerializer,
        responses={200: {
            'description': 'Ссылка на оплату',
            'example': {
                'url': 'https://checkout.stripe.com/pay/...',
                'payment_id': 1,
                'session_id': 'cs_test_...'
            }
        }}
    )
    @action(detail=False, methods=['post'], url_path='create-checkout')
    def create_checkout(self, request):
        """
        Создание сессии оплаты в Stripe
        """
        serializer = PaymentCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = request.user
        course_id = serializer.validated_data.get('course_id')
        lesson_id = serializer.validated_data.get('lesson_id')
        payment_method = serializer.validated_data.get('payment_method', 'stripe')

        # Получаем курс или урок
        if course_id:
            course = get_object_or_404(Course, id=course_id)
            product_name = course.title
            product_description = course.description
            amount = course.price if hasattr(course, 'price') else 1500.00
            metadata = {'course_id': course.id, 'type': 'course'}
        else:
            lesson = get_object_or_404(Lesson, id=lesson_id)
            product_name = lesson.title
            product_description = lesson.description
            amount = 500.00  # Фиксированная цена урока
            metadata = {'lesson_id': lesson.id, 'type': 'lesson'}

        # Проверяем, не оплачено ли уже
        existing_payment = Payment.objects.filter(
            user=user,
            paid_course_id=course_id if course_id else None,
            paid_lesson_id=lesson_id if lesson_id else None,
            status='paid'
        ).exists()

        if existing_payment:
            return Response(
                {'error': 'Этот курс/урок уже оплачен'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if payment_method == 'stripe':
            # Создаем продукт в Stripe
            product = StripeService.create_product(
                name=product_name,
                description=product_description,
                metadata=metadata
            )

            if not product:
                return Response(
                    {'error': 'Ошибка создания продукта в платежной системе'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            # Создаем цену
            price = StripeService.create_price(product.id, amount)

            if not price:
                return Response(
                    {'error': 'Ошибка создания цены в платежной системе'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            # Создаем URL для редиректа
            success_url = request.build_absolute_uri(
                reverse('stripe-payment-success') + '?session_id={CHECKOUT_SESSION_ID}'
            )
            cancel_url = request.build_absolute_uri(
                reverse('stripe-payment-cancel')
            )

            # Создаем сессию оплаты
            session = StripeService.create_checkout_session(
                price_id=price.id,
                success_url=success_url,
                cancel_url=cancel_url,
                metadata={
                    'user_id': user.id,
                    'user_email': user.email,
                    **metadata
                }
            )

            if not session:
                return Response(
                    {'error': 'Ошибка создания сессии оплаты'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            # Создаем запись о платеже в базе данных
            payment = Payment.objects.create(
                user=user,
                paid_course_id=course_id if course_id else None,
                paid_lesson_id=lesson_id if lesson_id else None,
                payment_amount=amount,
                payment_method='stripe',
                status='pending',
                stripe_product_id=product.id,
                stripe_price_id=price.id,
                stripe_session_id=session.id
            )

            return Response({
                'payment_id': payment.id,
                'session_id': session.id,
                'url': session.url,
                'message': 'Перейдите по ссылке для оплаты',
                'amount': amount,
                'currency': 'RUB'
            }, status=status.HTTP_201_CREATED)

        else:
            # Для других методов оплаты
            payment = Payment.objects.create(
                user=user,
                paid_course_id=course_id if course_id else None,
                paid_lesson_id=lesson_id if lesson_id else None,
                payment_amount=amount,
                payment_method=payment_method,
                status='pending'
            )

            return Response({
                'payment_id': payment.id,
                'message': 'Платеж создан (офлайн метод)',
                'amount': amount,
                'method': payment_method
            }, status=status.HTTP_201_CREATED)

    @extend_schema(
        summary="Проверить статус платежа",
        description="Проверяет статус платежа по ID сессии Stripe",
        parameters=[
            OpenApiParameter(
                name='session_id',
                type=str,
                location=OpenApiParameter.QUERY,
                description='ID сессии Stripe',
                required=True
            )
        ]
    )
    @action(detail=False, methods=['get'], url_path='check-status')
    def check_status(self, request):
        """
        Проверка статуса платежа
        """
        session_id = request.query_params.get('session_id')

        if not session_id:
            return Response(
                {'error': 'Необходим параметр session_id'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Получаем информацию из Stripe
        session = StripeService.retrieve_session(session_id)

        if not session:
            return Response(
                {'error': 'Сессия не найдена'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Обновляем статус платежа в базе данных
        try:
            payment = Payment.objects.get(stripe_session_id=session_id)

            if session.payment_status == 'paid' and payment.status != 'paid':
                payment.status = 'paid'
                payment.save()

                # Здесь можно добавить логику предоставления доступа
                # к курсу/уроку после успешной оплаты

            return Response({
                'session_id': session.id,
                'payment_status': session.payment_status,
                'amount_total': session.amount_total / 100,  # Конвертируем из копеек
                'currency': session.currency.upper(),
                'customer_email': session.customer_details.get('email') if session.customer_details else None,
                'payment_intent': session.payment_intent,
                'metadata': session.metadata,
                'local_payment_id': payment.id,
                'local_payment_status': payment.status
            })

        except Payment.DoesNotExist:
            return Response({
                'session_id': session.id,
                'payment_status': session.payment_status,
                'amount_total': session.amount_total / 100,
                'currency': session.currency.upper(),
                'message': 'Платеж найден в Stripe, но не найден в локальной базе'
            })

    @extend_schema(
        summary="Успешная оплата",
        description="Эндпоинт для редиректа после успешной оплаты"
    )
    @action(detail=False, methods=['get'], url_path='success', permission_classes=[])
    def payment_success(self, request):
        """
        Обработка успешной оплаты (редирект от Stripe)
        """
        session_id = request.query_params.get('session_id')

        if session_id:
            # Обновляем статус платежа
            session = StripeService.retrieve_session(session_id)
            if session and session.payment_status == 'paid':
                try:
                    payment = Payment.objects.get(stripe_session_id=session_id)
                    payment.status = 'paid'
                    payment.save()

                    return Response({
                        'success': True,
                        'message': 'Оплата прошла успешно!',
                        'payment_id': payment.id,
                        'session_id': session_id,
                        'details': 'Доступ к материалам предоставлен.'
                    })
                except Payment.DoesNotExist:
                    pass

        return Response({
            'success': True,
            'message': 'Оплата прошла успешно!'
        })

    @extend_schema(
        summary="Отмена оплаты",
        description="Эндпоинт для редиректа при отмене оплаты"
    )
    @action(detail=False, methods=['get'], url_path='cancel', permission_classes=[])
    def payment_cancel(self, request):
        """
        Обработка отмены оплаты (редирект от Stripe)
        """
        return Response({
            'message': 'Оплата отменена. Вы можете попробовать снова.',
            'status': 'cancelled'
        }, status=status.HTTP_200_OK)
