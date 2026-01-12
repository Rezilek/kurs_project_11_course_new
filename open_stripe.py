import stripe
from django.conf import settings
import os
import urllib.parse
import webbrowser

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

stripe.api_key = settings.STRIPE_SECRET_KEY

print('=' * 70)
print('АВТОМАТИЧЕСКОЕ ОТКРЫТИЕ ССЫЛКИ STRIPE')
print('=' * 70)

# Создаем новую сессию
session = stripe.checkout.Session.create(
    payment_method_types=['card'],
    line_items=[{
        'price': 'price_1SoSIsRON7W9ASizcOut2ujj',
        'quantity': 1,
    }],
    mode='payment',
    success_url='http://localhost:8000/api/users/payments/success/?session_id={CHECKOUT_SESSION_ID}',
    cancel_url='http://localhost:8000/api/users/payments/cancel/',
)

print(f'✅ Новая сессия создана: {session.id}')

# Варианты ссылок
urls = [
    # 1. Прямой вызов браузера через Python (самый надежный)
    session.url,
    
    # 2. Короткая версия
    f'https://checkout.stripe.com/pay/{session.id}',
    
    # 3. Закодированная версия для Windows
    urllib.parse.quote(session.url, safe=':/?&=#'),
]

print('\\n🔗 Попробуйте эти ссылки:')
for i, url in enumerate(urls, 1):
    print(f'{i}. {url[:80]}...')

print('\\n🖥️ Открываю в браузере...')

# Способ 1: Прямое открытие через webbrowser (самый надежный)
try:
    webbrowser.open(session.url)
    print('✅ Ссылка отправлена в браузер')
except:
    print('❌ Не удалось открыть через webbrowser')

# Способ 2: Для Windows - команда start
import subprocess
try:
    # Используем короткую ссылку для Windows
    short_url = f'https://checkout.stripe.com/pay/{session.id}'
    subprocess.run(['cmd', '/c', 'start', short_url], shell=True)
    print('✅ Открыто через Windows start')
except:
    print('❌ Не удалось открыть через start')

# Способ 3: Сохраняем в файл HTML
html_content = f'''
<!DOCTYPE html>
<html>
<head>
    <title>Stripe Checkout Test</title>
    <meta charset="utf-8">
</head>
<body style="padding: 20px; font-family: Arial;">
    <h2>Тест Stripe Checkout</h2>
    <p>Если ссылка не открывается напрямую, нажмите кнопку:</p>
    
    <button onclick="window.location.href='{session.url}'" 
            style="padding: 15px 30px; background: #635bff; color: white; border: none; border-radius: 8px; font-size: 16px; cursor: pointer;">
        🔗 Открыть Stripe Checkout
    </button>
    
    <p style="margin-top: 30px;">Или скопируйте ссылку:</p>
    <input type="text" value="{session.url}" style="width: 80%; padding: 10px; border: 1px solid #ccc;" readonly>
    
    <div style="margin-top: 30px; padding: 15px; background: #f5f5f5; border-radius: 8px;">
        <h3>Если все еще не работает:</h3>
        <ol>
            <li>Скопируйте ссылку выше</li>
            <li>Вставьте в адресную строку браузера ВРУЧНУЮ</li>
            <li>Нажмите Enter</li>
            <li>Или попробуйте на другом устройстве/браузере</li>
        </ol>
    </div>
</body>
</html>
'''

with open('stripe_test.html', 'w', encoding='utf-8') as f:
    f.write(html_content)

print('✅ HTML файл создан: stripe_test.html')
print('Откройте его в браузере')

print('\\n' + '=' * 70)
print('Ссылка для ручного копирования:')
print(session.url)
print('=' * 70)
