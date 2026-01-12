import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

import stripe
from django.conf import settings
import webbrowser

stripe.api_key = settings.STRIPE_SECRET_KEY

print('=' * 70)
print('ЬЫ ТСТ С  URL')
print('=' * 70)

# спользуем прямой URL для редиректов
success_url = 'http://localhost:8000/api/users/payments/success/?session_id={CHECKOUT_SESSION_ID}'
cancel_url = 'http://localhost:8000/api/users/payments/cancel/'

print(f'Success URL: {success_url}')
print(f'Cancel URL: {cancel_url}')

print('\nсправьте users/urls.py - порядок важен:')
print('1. Сначала path(\"payments/success/\", payment_success)')
print('2. отом path(\"\", include(router.urls))')

try:
    # Создаем сессию
    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=[{
            'price': 'price_1SoSIsRON7W9ASizcOut2ujj',
            'quantity': 1,
        }],
        mode='payment',
        success_url=success_url,
        cancel_url=cancel_url,
    )
    
    print(f'\n✅ Сессия создана!')
    print(f'ID: {session.id}')
    
    print('\n' + '=' * 70)
    print(f'Ссылка для оплаты:')
    print(f'https://checkout.stripe.com/pay/{session.id}')
    print('=' * 70)
    
    # оказываем куда будет редирект
    final_url = success_url.replace('{CHECKOUT_SESSION_ID}', session.id)
    print(f'\nосле оплаты Stripe перенаправит на:')
    print(f'{final_url}')
    
    # ткрываем
    webbrowser.open(f'https://checkout.stripe.com/pay/{session.id}')
    
    print('\n🔥 : бедитесь, что в users/urls.py:')
    print('path(\"payments/success/\", payment_success) идет  include(router.urls)')
    
except Exception as e:
    print(f'❌ шибка: {e}')
    import traceback
    traceback.print_exc()
