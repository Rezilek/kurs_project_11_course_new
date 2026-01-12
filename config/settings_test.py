import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

#  для тестирования - потом удалите эти ключи!
SECRET_KEY = 'test-key-for-development-only-12345'
DEBUG = True
ALLOWED_HOSTS = ['localhost', '127.0.0.1']

# Ы TEST ключи Stripe - создайте новые тестовые в Stripe Dashboard
STRIPE_SECRET_KEY = 'sk_test_...вставьте_тестовый_ключ...'
STRIPE_PUBLISHABLE_KEY = 'pk_test_...вставьте_тестовый_ключ...'

# стальные настройки...
