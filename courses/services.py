import stripe
from django.conf import settings
from django.shortcuts import get_object_or_404
from .models import Course, Payment

# Инициализация Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY


def create_stripe_product(course):
    """Создает продукт в Stripe на основе курса"""
    try:
        # Проверяем, существует ли уже продукт для этого курса
        existing_products = stripe.Product.search(
            query=f"metadata['course_id']:'{course.id}'"
        )

        if existing_products and len(existing_products.data) > 0:
            print(f"Продукт для курса {course.id} уже существует")
            return existing_products.data[0]

        # Создаем новый продукт
        product = stripe.Product.create(
            name=course.title[:255],  # Stripe ограничение 255 символов
            description=course.description[:500] if course.description else f"Курс: {course.title}",
            metadata={
                'course_id': str(course.id),
                'course_title': course.title[:100],
            },
            default_price_data={  # Можно сразу создать цену
                'currency': 'rub',
                'unit_amount': int(course.price * 100) if hasattr(course, 'price') else 100000,  # 1000 руб по умолчанию
            }
        )
        return product
    except stripe.error.StripeError as e:
        print(f"Ошибка создания продукта в Stripe: {e}")
        return None


def create_stripe_price(product, amount, currency='rub'):
    """Создает цену для продукта в Stripe"""
    try:
        # Конвертируем в минимальные единицы валюты
        if currency.lower() == 'rub':
            amount_in_cents = int(float(amount) * 100)  # рубли в копейки
        elif currency.lower() == 'usd':
            amount_in_cents = int(float(amount) * 100)  # доллары в центы
        else:
            amount_in_cents = int(float(amount) * 100)  # по умолчанию

        # Создаем цену
        price = stripe.Price.create(
            product=product.id,
            unit_amount=amount_in_cents,
            currency=currency,
            metadata={
                'course_id': product.metadata.get('course_id'),
                'original_amount': str(amount),
            }
        )
        return price
    except stripe.error.StripeError as e:
        print(f"Ошибка создания цены в Stripe: {e}")
        return None


def create_stripe_checkout_session(price_id, course, user, success_url=None, cancel_url=None):
    """Создает сессию оплаты в Stripe"""
    try:
        # URL по умолчанию
        if not success_url:
            success_url = f"{settings.FRONTEND_URL or 'http://localhost:8000'}/api/courses/payment/success/?session_id={{CHECKOUT_SESSION_ID}}"
        if not cancel_url:
            cancel_url = f"{settings.FRONTEND_URL or 'http://localhost:8000'}/api/courses/payment/cancel/"

        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[
                {
                    'price': price_id,
                    'quantity': 1,
                },
            ],
            mode='payment',
            success_url=success_url,
            cancel_url=cancel_url,
            client_reference_id=str(user.id),
            customer_email=user.email,
            metadata={
                'course_id': str(course.id),
                'course_title': course.title,
                'user_id': str(user.id),
                'user_email': user.email,
            },
            payment_intent_data={
                'metadata': {
                    'course_id': str(course.id),
                    'user_id': str(user.id),
                }
            }
        )
        return checkout_session
    except stripe.error.StripeError as e:
        print(f"Ошибка создания сессии оплаты в Stripe: {e}")
        return None


def get_stripe_session_status(session_id):
    """Получает статус сессии оплаты из Stripe"""
    try:
        session = stripe.checkout.Session.retrieve(
            session_id,
            expand=['payment_intent']  # Получаем дополнительную информацию
        )

        return {
            'id': session.id,
            'status': session.payment_status,
            'amount_total': session.amount_total / 100,  # Конвертируем обратно
            'currency': session.currency,
            'customer_email': session.customer_details.get('email') if session.customer_details else None,
            'metadata': session.metadata,
            'payment_intent_id': session.payment_intent.id if session.payment_intent else None,
            'payment_intent_status': session.payment_intent.status if session.payment_intent else None,
        }
    except stripe.error.StripeError as e:
        print(f"Ошибка получения статуса сессии: {e}")
        return None


def handle_payment_expired(session):
    pass


def handle_payment_intent_success(payment_intent):
    pass


def handle_payment_intent_failed(payment_intent):
    pass


def handle_stripe_webhook(payload, sig_header):
    """Обработка вебхуков от Stripe"""
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        print(f"Неверный payload: {e}")
        return None
    except stripe.error.SignatureVerificationError as e:
        print(f"Неверная подпись: {e}")
        return None

    # Обработка различных событий
    event_type = event['type']

    if event_type == 'checkout.session.completed':
        session = event['data']['object']
        return handle_payment_success(session)

    elif event_type == 'checkout.session.expired':
        session = event['data']['object']
        return handle_payment_expired(session)

    elif event_type == 'payment_intent.succeeded':
        payment_intent = event['data']['object']
        return handle_payment_intent_success(payment_intent)

    elif event_type == 'payment_intent.payment_failed':
        payment_intent = event['data']['object']
        return handle_payment_intent_failed(payment_intent)

    return None


def handle_payment_success(session):
    """Обработка успешной оплаты"""
    try:
        # Находим платеж по session_id
        payment = Payment.objects.get(stripe_session_id=session['id'])

        # Обновляем статус
        payment.status = 'paid'
        payment.stripe_payment_intent_id = session.get('payment_intent')
        payment.save()

        # TODO: Здесь можно добавить логику предоставления доступа к курсу
        # Например, создать запись о покупке или добавить пользователя в группу

        return {
            'success': True,
            'payment_id': payment.id,
            'course_id': payment.course.id if payment.course else None,
            'user_id': payment.user.id,
        }
    except Payment.DoesNotExist:
        print(f"Платеж с session_id={session['id']} не найден")
        return None


def create_stripe_customer(user):
    """Создает клиента в Stripe"""
    try:
        # Проверяем, существует ли уже клиент
        existing_customers = stripe.Customer.search(
            query=f"email:'{user.email}'"
        )

        if existing_customers and len(existing_customers.data) > 0:
            return existing_customers.data[0]

        # Создаем нового клиента
        customer = stripe.Customer.create(
            email=user.email,
            name=user.get_full_name() or user.email,
            metadata={
                'user_id': str(user.id),
                'username': user.username,
            }
        )
        return customer
    except stripe.error.StripeError as e:
        print(f"Ошибка создания клиента Stripe: {e}")
        return None
    