import stripe
from django.conf import settings
import os

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

stripe.api_key = settings.STRIPE_SECRET_KEY

print('=' * 60)
print('ПРОВЕРКА СТАТУСА STRIPE')
print('=' * 60)

# 1. Проверяем ключи
print('1. Проверка ключей:')
print(f'   Secret Key: {stripe.api_key[:20]}...')
print(f'   Publishable Key: {settings.STRIPE_PUBLISHABLE_KEY[:20]}...')

# Проверяем режим ключа
if stripe.api_key.startswith('sk_test_'):
    print('   ✅ Тестовый режим (sk_test_)')
elif stripe.api_key.startswith('sk_live_'):
    print('   ❌ ПРОДАКШН режим (sk_live_)!')
else:
    print('   ⚠️ Неизвестный формат ключа')

print()

# 2. Проверяем аккаунт
print('2. Проверка аккаунта:')
try:
    account = stripe.Account.retrieve()
    print(f'   ✅ Аккаунт доступен')
    print(f'   Email: {account.get("email", "N/A")}')
    print(f'   Страна: {account.get("country", "N/A")}')
except stripe.error.AuthenticationError:
    print('   ❌ Ошибка аутентификации - неверный ключ')
except Exception as e:
    print(f'   ❌ Ошибка: {e}')

print()

# 3. Проверяем цену
print('3. Проверка цены:')
price_id = 'price_1SoSIsRON7W9ASizcOut2ujj'
try:
    price = stripe.Price.retrieve(price_id)
    print(f'   ✅ Цена найдена: {price.id}')
    print(f'   Активна: {price.active}')
    print(f'   Сумма: {price.unit_amount/100} {price.currency.upper()}')
    
    # Проверяем продукт
    product = stripe.Product.retrieve(price.product)
    print(f'   ✅ Продукт: {product.name}')
    print(f'   Активен: {product.active}')
except stripe.error.InvalidRequestError:
    print(f'   ❌ Цена {price_id} не найдена!')
except Exception as e:
    print(f'   ❌ Ошибка: {e}')

print()

# 4. Проверяем последнюю сессию
print('4. Проверка последней сессии:')
try:
    from users.models import Payment
    payment = Payment.objects.order_by('-created_at').first()
    
    if payment and payment.stripe_session_id:
        session_id = payment.stripe_session_id
        print(f'   Последний платеж ID: {payment.id}')
        print(f'   Session ID: {session_id}')
        
        # Получаем сессию из Stripe
        session = stripe.checkout.Session.retrieve(session_id)
        print(f'   ✅ Сессия найдена в Stripe')
        print(f'   Статус: {session.status}')
        print(f'   Payment Status: {session.payment_status}')
        print(f'   Live Mode: {session.livemode}')
        print(f'   Expires: {session.expires_at}')
        
        if session.livemode:
            print('   ⚠️  ВНИМАНИЕ: Сессия в LIVE режиме!')
            print('      Проверьте: https://dashboard.stripe.com/')
        else:
            print('   ✅ Сессия в TEST режиме')
            print('      Панель: https://dashboard.stripe.com/test/')
            
    else:
        print('   Нет платежей с session_id')
        
except ImportError:
    print('   ❌ Не могу импортировать модели')
except Exception as e:
    print(f'   ❌ Ошибка: {e}')

print()
print('=' * 60)
print('СОВЕТЫ:')
print('1. Если сессия в LIVE режиме - откройте Live Dashboard')
print('2. Если сессия в TEST режиме - откройте Test Dashboard')
print('3. Проверьте Events в Dashboard: https://dashboard.stripe.com/test/events')
print('=' * 60)
