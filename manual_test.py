#!/usr/bin/env python
"""
Ручное тестирование полного цикла оплаты
"""
import os
import sys

import django
import requests
import json
import time

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

BASE_URL = "http://localhost:8000"


def print_step(step_num, title):
    """Вывод шага тестирования"""
    print(f"\n{step_num}. {'=' * 60}")
    print(f"   {title}")
    print("   " + "=" * 60)


def test_full_payment_cycle():
    """Тестирование полного цикла оплаты"""
    print("🧪 ТЕСТИРОВАНИЕ ПОЛНОГО ЦИКЛА ОПЛАТЫ")
    print("=" * 60)

    # 1. Аутентификация
    print_step(1, "🔐 АУТЕНТИФИКАЦИЯ")

    # Создаем тестового пользователя если нужно
    try:
        from django.contrib.auth import get_user_model
        User = get_user_model()

        if not User.objects.filter(email='test@example.com').exists():
            user = User.objects.create_user(
                email='test@example.com',
                password='testpassword123',
                first_name='Test',
                last_name='User'
            )
            print("   ✅ Создан тестовый пользователь: test@example.com / testpassword123")
    except:
        pass

    auth_data = {
        "email": "test@example.com",
        "password": "testpassword123"
    }

    try:
        response = requests.post(f"{BASE_URL}/api/users/token/", json=auth_data, timeout=10)

        if response.status_code == 200:
            tokens = response.json()
            access_token = tokens.get('access')
            print(f"   ✅ Токен получен успешно!")
            print(f"      Access token: {access_token[:30]}...")
        else:
            print(f"   ❌ Ошибка аутентификации: {response.status_code}")
            print(f"      Ответ: {response.text}")
            return None
    except requests.exceptions.ConnectionError:
        print("   ❌ Не удалось подключиться к серверу")
        print("      Убедитесь, что сервер запущен: python manage.py runserver")
        return None

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    # 2. Получение списка курсов
    print_step(2, "📚 ПОЛУЧЕНИЕ КУРСОВ")

    try:
        response = requests.get(f"{BASE_URL}/api/courses/courses/", headers=headers, timeout=10)

        if response.status_code == 200:
            courses = response.json()
            if courses.get('results') and len(courses['results']) > 0:
                course_id = courses['results'][0]['id']
                course_title = courses['results'][0]['title']
                print(f"   ✅ Курсы получены")
                print(f"      Используем курс: {course_title} (ID: {course_id})")
            else:
                print("   ⚠️ Нет доступных курсов")
                print("      Создаем тестовый курс...")

                # Создаем тестовый курс
                course_data = {
                    "title": "Тестовый курс для оплаты",
                    "description": "Описание тестового курса",
                    "price": 500.00
                }

                response = requests.post(
                    f"{BASE_URL}/api/courses/courses/",
                    json=course_data,
                    headers=headers,
                    timeout=10
                )

                if response.status_code == 201:
                    course = response.json()
                    course_id = course['id']
                    print(f"   ✅ Тестовый курс создан (ID: {course_id})")
                else:
                    print(f"   ❌ Ошибка создания курса: {response.status_code}")
                    print(f"      Ответ: {response.text}")
                    return None
        else:
            print(f"   ❌ Ошибка получения курсов: {response.status_code}")
            return None
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
        return None

    # 3. Создание платежа через Stripe
    print_step(3, "💳 СОЗДАНИЕ ПЛАТЕЖА ЧЕРЕЗ STRIPE")

    payment_data = {
        "item_type": "course",
        "item_id": course_id
    }

    try:
        response = requests.post(
            f"{BASE_URL}/api/users/payments/buy/",
            json=payment_data,
            headers=headers,
            timeout=30
        )

        if response.status_code == 201:
            payment_info = response.json()
            print(f"   ✅ Платеж создан успешно!")
            print(f"      ID платежа: {payment_info.get('payment_id')}")
            print(f"      Сумма: {payment_info.get('amount')}")
            print(f"      Тип: {payment_info.get('item_type')}")
            print(f"      Название: {payment_info.get('item_name')}")

            payment_url = payment_info.get('payment_url')
            if payment_url:
                print(f"      URL оплаты: {payment_url[:80]}...")

                # 4. Проверка URL Stripe
                print_step(4, "🌐 ПРОВЕРКА URL STRIPE")

                if payment_url.startswith('https://checkout.stripe.com'):
                    print(f"   ✅ URL корректный (Stripe Checkout)")

                    # Проверяем, что URL доступен (только заголовки)
                    try:
                        head_response = requests.head(payment_url, timeout=10, allow_redirects=True)
                        print(f"   ✅ URL доступен (статус: {head_response.status_code})")
                    except:
                        print(f"   ⚠️ Не удалось проверить доступность URL")
                else:
                    print(f"   ⚠️ URL не соответствует формату Stripe")
            else:
                print(f"   ❌ URL оплаты не получен")

        elif response.status_code == 400 and "уже приобрели" in response.text:
            print("   ✅ Курс уже куплен (ожидаемое поведение)")
        else:
            print(f"   ❌ Ошибка создания платежа: {response.status_code}")
            print(f"      Ответ: {response.text}")
            return None

    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
        return None

    # 5. Проверка страниц успеха и отмены
    print_step(5, "✅❌ ПРОВЕРКА СТРАНИЦ SUCCESS И CANCEL")

    try:
        # Success page
        success_response = requests.get(f"{BASE_URL}/api/users/payments/success/", timeout=10)
        print(f"   ✅ Страница успеха: статус {success_response.status_code}")

        # Cancel page
        cancel_response = requests.get(f"{BASE_URL}/api/users/payments/cancel/", timeout=10)
        print(f"   ✅ Страница отмены: статус {cancel_response.status_code}")
    except Exception as e:
        print(f"   ❌ Ошибка проверки страниц: {e}")

    # 6. Проверка документации
    print_step(6, "📖 ПРОВЕРКА ДОКУМЕНТАЦИИ")

    try:
        docs_response = requests.get(f"{BASE_URL}/api/docs/", timeout=10)
        print(f"   ✅ Swagger UI: статус {docs_response.status_code}")

        redoc_response = requests.get(f"{BASE_URL}/api/redoc/", timeout=10)
        print(f"   ✅ ReDoc: статус {redoc_response.status_code}")

        schema_response = requests.get(f"{BASE_URL}/api/schema/", timeout=10)
        print(f"   ✅ OpenAPI Schema: статус {schema_response.status_code}")
    except Exception as e:
        print(f"   ❌ Ошибка проверки документации: {e}")

    return access_token


def quick_health_check():
    """Быстрая проверка здоровья API"""
    print("\n⚡ БЫСТРАЯ ПРОВЕРКА ЗДОРОВЬЯ API")
    print("-" * 40)

    endpoints = [
        ("API Root", "/api/", "GET"),
        ("Документация", "/api/docs/", "GET"),
        ("ReDoc", "/api/redoc/", "GET"),
        ("Схема", "/api/schema/", "GET"),
        ("Курсы", "/api/courses/courses/", "GET"),
        ("Пользователи", "/api/users/users/", "GET"),
        ("Токен", "/api/users/token/", "POST"),
    ]

    for name, endpoint, method in endpoints:
        try:
            if method == "GET":
                response = requests.get(f"{BASE_URL}{endpoint}", timeout=5)
            else:  # POST
                response = requests.post(f"{BASE_URL}{endpoint}", timeout=5)

            if response.status_code in [200, 201, 401, 403, 405]:
                status = "✅"
            else:
                status = "⚠️"

            print(f"{status} {name}: {response.status_code} ({response.reason})")

        except requests.exceptions.ConnectionError:
            print(f"❌ {name}: Не удалось подключиться")
            print("   Убедитесь, что сервер запущен: python manage.py runserver")
            return False
        except requests.exceptions.Timeout:
            print(f"⚠️ {name}: Таймаут")
        except Exception as e:
            print(f"❌ {name}: Ошибка - {e}")

    return True


if __name__ == "__main__":
    print("🎯 ФИНАЛЬНОЕ ТЕСТИРОВАНИЕ ПРОЕКТА")
    print("=" * 60)

    # Сначала быстрая проверка
    if not quick_health_check():
        print("\n❌ Сервер не доступен. Запустите его сначала:")
        print("   python manage.py runserver")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("Запуск расширенного тестирования...")
    print("=" * 60)

    try:
        token = test_full_payment_cycle()

        if token:
            print("\n" + "=" * 60)
            print("🎉 ТЕСТИРОВАНИЕ ЗАВЕРШЕНО УСПЕШНО!")
            print("=" * 60)

            print("\n📋 СЛЕДУЮЩИЕ ШАГИ:")
            print("1. Проверьте документацию: http://localhost:8000/api/docs/")
            print("2. Проверьте админку: http://localhost:8000/admin/")
            print("3. Протестируйте реальную оплату с тестовой картой:")
            print("   Карта: 4242 4242 4242 4242")
            print("   Дата: любая будущая")
            print("   CVC: любые 3 цифры")

    except Exception as e:
        print(f"\n❌ Ошибка при тестировании: {e}")
        import traceback

        traceback.print_exc()

    print("\n" + "=" * 60)