import stripe
from django.conf import settings
import webbrowser
import time
import os

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

stripe.api_key = settings.STRIPE_SECRET_KEY

print('=' * 70)
print('СОЗДАНИЕ НОВОЙ СЕССИИ STRIPE CHECKOUT')
print('=' * 70)

try:
    # 1. Создаем сессию с полными настройками
    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=[{
            'price': 'price_1SoSIsRON7W9ASizcOut2ujj',
            'quantity': 1,
        }],
        mode='payment',
        success_url='http://localhost:8000/api/users/payments/success/?session_id={CHECKOUT_SESSION_ID}',
        cancel_url='http://localhost:8000/api/users/payments/cancel/',
        client_reference_id='test_' + str(int(time.time())),
        customer_email='test@example.com',
        metadata={
            'test': 'true',
            'source': 'django_test'
        }
    )
    
    print('✅ Сессия создана успешно!')
    print(f'Время: {time.strftime("%H:%M:%S")}')
    print(f'Session ID: {session.id}')
    print(f'URL: {session.url[:100]}...')
    
    # 2. Сохраняем все возможные ссылки
    urls = [
        session.url,
        f'https://checkout.stripe.com/pay/{session.id}',
        f'https://checkout.stripe.com/c/pay/{session.id}',
        f'https://checkout.stripe.com/c/pay/{session.id}?key={settings.STRIPE_PUBLISHABLE_KEY}'
    ]
    
    print('\n🔗 ВАРИАНТЫ ССЫЛОК:')
    for i, url in enumerate(urls, 1):
        print(f'{i}. {url[:80]}...')
    
    # 3. Проверяем сессию через API
    print('\n📋 ПРОВЕРКА СЕССИИ ЧЕРЕЗ API:')
    retrieved = stripe.checkout.Session.retrieve(session.id)
    print(f'Статус: {retrieved.status}')
    print(f'Payment Status: {retrieved.payment_status}')
    print(f'Expires: {retrieved.expires_at}')
    print(f'URL доступен: {retrieved.url is not None}')
    
    # 4. Пробуем открыть
    print('\n🖥️ ОТКРЫВАЕМ В БРАУЗЕРЕ...')
    
    # Самая простая ссылка
    simple_url = f'https://checkout.stripe.com/pay/{session.id}'
    print(f'Используем: {simple_url}')
    
    # Открываем
    webbrowser.open(simple_url)
    
    # 5. Для ручного копирования
    print('\n' + '=' * 70)
    print(f'https://checkout.stripe.com/pay/{session.id}')
    print('=' * 70)
    
    print('\n💡 СОВЕТ: Попробуйте открыть ссылку в:')
    print('1. Режиме инкогнито (Ctrl+Shift+N)')
    print('2. Другом браузере')
    print('3. На телефоне')
    print('4. С отключенными расширениями')
    
except Exception as e:
    print(f'❌ Ошибка: {e}')
    import traceback
    traceback.print_exc()
