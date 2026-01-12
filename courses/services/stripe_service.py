import stripe
from django.conf import settings
import logging

logger = logging.getLogger(__name__)
stripe.api_key = settings.STRIPE_SECRET_KEY

class StripeService:
    """Сервис для работы с платежами Stripe"""
    
    @staticmethod
    def create_product(name, description=None):
        """Создание продукта в Stripe"""
        try:
            product = stripe.Product.create(
                name=name,
                description=description or name,
                metadata={'type': 'course'}
            )
            return product
        except stripe.error.StripeError as e:
            logger.error(f"Ошибка создания продукта Stripe: {e}")
            raise
    
    @staticmethod
    def create_price(product_id, amount, currency='rub'):
        """Создание цены в Stripe"""
        try:
            # онвертируем в центы/копейки
            amount_in_cents = int(amount * 100)
            
            price = stripe.Price.create(
                unit_amount=amount_in_cents,
                currency=currency.lower(),
                product=product_id,
            )
            return price
        except stripe.error.StripeError as e:
            logger.error(f"Ошибка создания цены Stripe: {e}")
            raise
    
    @staticmethod
    def create_checkout_session(price_id, user_id, item_id, item_type='course', 
                                success_url=None, cancel_url=None):
        """Создание сессии для оплаты"""
        try:
            session = stripe.checkout.Session.create(
                line_items=[{
                    'price': price_id,
                    'quantity': 1,
                }],
                mode='payment',
                success_url=success_url or f'http://localhost:8000/api/users/payments/success/?session_id={{CHECKOUT_SESSION_ID}}',
                cancel_url=cancel_url or 'http://localhost:8000/api/users/payments/cancel/',
                metadata={
                    'user_id': str(user_id),
                    'item_id': str(item_id),
                    'item_type': item_type,
                },
                payment_method_types=['card'],
            )
            return session
        except stripe.error.StripeError as e:
            logger.error(f"Ошибка создания сессии Stripe: {e}")
            raise
    
    @staticmethod
    def retrieve_session(session_id):
        """олучение информации о сессии"""
        try:
            session = stripe.checkout.Session.retrieve(session_id)
            return session
        except stripe.error.StripeError as e:
            logger.error(f"Ошибка получения сессии Stripe: {e}")
            raise
