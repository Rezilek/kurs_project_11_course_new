# users/api_views.py
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


@extend_schema(
    summary="Успешная оплата",
    description="API эндпоинт для обработки успешного редиректа от Stripe",
    tags=['Платежи'],
    methods=['GET'],
    responses={
        200: {
            'type': 'object',
            'properties': {
                'status': {'type': 'string', 'example': 'success'},
                'payment_id': {'type': 'integer', 'example': 123},
                'item_name': {'type': 'string', 'example': 'Название курса'},
                'amount': {'type': 'number', 'example': 1999.99},
                'currency': {'type': 'string', 'example': 'rub'}
            }
        }
    }
)
@api_view(['GET'])
@permission_classes([AllowAny])
def api_payment_success(request):
    """
    API эндпоинт для успешной оплаты
    """
    session_id = request.GET.get('session_id')

    if not session_id:
        return Response(
            {'error': 'Отсутствует session_id'},
            status=400
        )

    from .models import Payment
    try:
        payment = Payment.objects.get(stripe_session_id=session_id)

        if payment.paid_course:
            item_name = payment.paid_course.title
        elif payment.paid_lesson:
            item_name = payment.paid_lesson.title
        else:
            item_name = "Неизвестный товар"

        return Response({
            'status': 'success',
            'payment_id': payment.id,
            'item_name': item_name,
            'amount': float(payment.amount),
            'currency': payment.currency,
            'session_id': session_id
        })

    except Payment.DoesNotExist:
        return Response(
            {'error': f'Платеж с session_id {session_id} не найден'},
            status=404
        )


@extend_schema(
    summary="Отмена оплаты",
    description="API эндпоинт для обработки отмены оплаты",
    tags=['Платежи'],
    methods=['GET'],
    responses={
        200: {
            'type': 'object',
            'properties': {
                'status': {'type': 'string', 'example': 'cancelled'},
                'message': {'type': 'string', 'example': 'Оплата отменена'},
                'session_id': {'type': 'string', 'example': 'cs_test_...'}
            }
        }
    }
)
@api_view(['GET'])
@permission_classes([AllowAny])
def api_payment_cancel(request):
    """
    API эндпоинт для отмены оплаты
    """
    session_id = request.GET.get('session_id')

    return Response({
        'status': 'cancelled',
        'message': 'Оплата была отменена пользователем',
        'session_id': session_id or 'не указан'
    })