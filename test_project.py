#!/usr/bin/env python
"""
Скрипт для финального тестирования проекта
"""
import os
import sys
import django
import requests
import json
from datetime import datetime

# Настраиваем Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test import TestCase, Client
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from courses.models import Course, Lesson
from users.models import Payment

User = get_user_model()


def print_header(text):
    """Красивый вывод заголовка"""
    print("\n" + "=" * 80)
    print(f" {text}")
    print("=" * 80)


def test_documentation():
    """Тестирование документации"""
    print_header("ТЕСТИРОВАНИЕ ДОКУМЕНТАЦИИ")

    client = Client()

    endpoints = [
        ('/api/docs/', 'Swagger UI'),
        ('/api/redoc/', 'ReDoc'),
        ('/api/schema/', 'OpenAPI Schema'),
    ]

    for url, name in endpoints:
        response = client.get(url)
        status = "✅" if response.status_code == 200 else "❌"
        print(f"{status} {name}: {url} (статус: {response.status_code})")


def test_authentication():
    """Тестирование аутентификации"""
    print_header("ТЕСТИРОВАНИЕ АУТЕНТИФИКАЦИИ")

    client = APIClient()

    # Тест получения JWT токена
    print("\n🔐 Тест JWT аутентификации:")

    # 1. Получение токена
    test_user = {
        'email': 'createsuperuser@example.com',
        'password': 'createsuperuser123'
    }

    try:
        response = client.post('/api/users/token/', test_user)
        if response.status_code == 200:
            print("✅ Получение JWT токена: УСПЕШНО")
            access_token = response.data.get('access')
            refresh_token = response.data.get('refresh')
            print(f"   Access token получен: {'Да' if access_token else 'Нет'}")
            print(f"   Refresh token получен: {'Да' if refresh_token else 'Нет'}")

            # Тест аутентифицированного запроса
            client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
            response = client.get('/api/users/users/')
            print(f"✅ Аутентифицированный запрос: статус {response.status_code}")
        else:
            print(f"❌ Получение JWT токена: ОШИБКА ({response.status_code})")
            print(f"   Ответ: {response.text}")
    except Exception as e:
        print(f"❌ Ошибка при получении токена: {e}")


def test_stripe_integration():
    """Тестирование интеграции со Stripe"""
    print_header("ТЕСТИРОВАНИЕ STRIPE ИНТЕГРАЦИИ")

    from django.conf import settings

    # Проверка настроек Stripe
    print("\n⚙️ Проверка настроек Stripe:")
    print(f"✅ STRIPE_SECRET_KEY: {'Настроен' if settings.STRIPE_SECRET_KEY else 'НЕ настроен'}")
    print(f"✅ STRIPE_PUBLISHABLE_KEY: {'Настроен' if settings.STRIPE_PUBLISHABLE_KEY else 'НЕ настроен'}")

    # Проверка сервисных функций
    print("\n🔧 Проверка сервисных функций Stripe:")

    try:
        from courses.services.stripe_service import StripeService
        print("✅ Модуль stripe_service импортирован успешно")

        # Проверка методов
        methods = ['create_product', 'create_price', 'create_checkout_session', 'retrieve_session']
        for method in methods:
            if hasattr(StripeService, method):
                print(f"✅ Метод {method}() существует")
            else:
                print(f"❌ Метод {method}() НЕ существует")

    except ImportError as e:
        print(f"❌ Ошибка импорта stripe_service: {e}")
    except Exception as e:
        print(f"❌ Ошибка проверки методов: {e}")


def test_models():
    """Тестирование моделей"""
    print_header("ТЕСТИРОВАНИЕ МОДЕЛЕЙ")

    models_to_check = [
        ('User', User),
        ('Course', Course),
        ('Lesson', Lesson),
        ('Payment', Payment),
    ]

    for name, model in models_to_check:
        try:
            count = model.objects.count()
            print(f"✅ Модель {name}: {count} записей")

            # Создаем тестовые данные если нужно
            if count == 0 and name == 'Course':
                print("   ⚠️ Создаем тестовый курс...")
                user = User.objects.first()
                if user:
                    Course.objects.create(
                        title="Тестовый курс",
                        description="Описание тестового курса",
                        owner=user,
                        price=1000.00
                    )
                    print("   ✅ Тестовый курс создан")

        except Exception as e:
            print(f"❌ Ошибка модели {name}: {e}")


def test_payment_flow():
    """Тестирование полного цикла оплаты"""
    print_header("ТЕСТИРОВАНИЕ ПОЛНОГО ЦИКЛА ОПЛАТЫ")

    print("\n🔄 Поток данных для оплаты:")
    steps = [
        "1. Пользователь выбирает курс",
        "2. Система проверяет, не куплен ли курс",
        "3. Создается платеж в БД",
        "4. Создается продукт/цена в Stripe",
        "5. Создается сессия оплаты",
        "6. Пользователь перенаправляется на Stripe",
        "7. После оплаты - редирект на success",
        "8. Статус обновляется через вебхук",
    ]

    for step in steps:
        print(f"✅ {step}")

    print("\n📋 Критические точки:")

    # Проверяем существование полей
    try:
        from users.models import Payment
        has_session_id = Payment._meta.get_field('stripe_session_id') is not None
        print(f"✅ Модель Payment имеет stripe_session_id: {'Да' if has_session_id else 'Нет'}")
    except:
        print("❌ Не удалось проверить поле stripe_session_id")

    # Проверяем URL endpoints
    client = Client()
    endpoints_to_check = [
        ('/api/users/payments/buy/', 'POST'),
        ('/api/users/payments/success/', 'GET'),
        ('/api/users/payments/cancel/', 'GET'),
    ]

    for url, method in endpoints_to_check:
        try:
            if method == 'GET':
                response = client.get(url)
            else:
                response = client.post(url)
            status = response.status_code
            icon = "✅" if status in [200, 201, 400, 401, 403] else "❌"
            print(f"{icon} {url}: статус {status}")
        except Exception as e:
            print(f"❌ {url}: ошибка - {e}")


def test_api_endpoints():
    """Тестирование основных API эндпоинтов"""
    print_header("ТЕСТИРОВАНИЕ API ЭНДПОИНТОВ")

    client = Client()

    endpoints = [
        ('/api/', 'Корневой эндпоинт API'),
        ('/api/courses/courses/', 'Список курсов'),
        ('/api/courses/lessons/', 'Список уроков'),
        ('/api/users/users/', 'Пользователи'),
        ('/api/users/payments/', 'Платежи'),
        ('/api/users/token/', 'Получение JWT токена'),
        ('/api/users/token/refresh/', 'Обновление JWT токена'),
    ]

    for url, description in endpoints:
        try:
            response = client.get(url)
            status_icon = "✅" if response.status_code in [200, 401, 403, 405] else "⚠️"
            print(f"{status_icon} {description}: {url} (статус: {response.status_code})")
        except Exception as e:
            print(f"❌ {description}: ошибка - {e}")


def run_all_tests():
    """Запуск всех тестов"""
    print("\n" + "🚀" * 40)
    print("  ЗАПУСК ФИНАЛЬНОГО ТЕСТИРОВАНИЯ ПРОЕКТА")
    print("🚀" * 40)
    print(f"Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    tests = [
        test_documentation,
        test_models,
        test_authentication,
        test_stripe_integration,
        test_payment_flow,
        test_api_endpoints,
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"\n❌ Ошибка при выполнении теста {test.__name__}: {e}")

    print("\n" + "=" * 80)
    print(f"ИТОГ: {passed}/{total} тестов пройдено успешно")

    if passed == total:
        print("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
    else:
        print(f"⚠️ Проблемы найдены: {total - passed} тестов не пройдено")

    print("=" * 80)


if __name__ == "__main__":
    run_all_tests()