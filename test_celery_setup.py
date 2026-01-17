import os
import sys
import django

# Настройка окружения Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.contrib.auth import get_user_model
from courses.models import Course, Subscription, Lesson

User = get_user_model()


def create_test_data():
    """
    Создаёт тестовые данные для проверки работы Celery.
    """
    print("=" * 60)
    print("Создание тестовых данных для проверки Celery...")
    print("=" * 60)

    # 1. СОЗДАНИЕ/ПОИСК ТЕСТОВОГО ПОЛЬЗОВАТЕЛЯ
    try:
        user = User.objects.get(email='celery_test@example.com')
        print(f"✅ Тестовый пользователь найден: {user.email}")
    except User.DoesNotExist:
        user = User.objects.create_user(
            email='celery_test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User',
            is_active=True,
            city='Test City'
        )
        print(f"✅ Тестовый пользователь создан: {user.email}")

    # 2. СОЗДАНИЕ/ПОИСК ТЕСТОВОГО КУРСА (с обязательными полями из вашей модели)
    try:
        # Пытаемся найти существующий курс
        course = Course.objects.get(
            title='Тестовый курс для Celery',
            owner=user
        )
        print(f"✅ Тестовый курс найден: {course.title}")
    except Course.DoesNotExist:
        # Создаём новый курс, указывая ВСЕ обязательные поля
        course = Course.objects.create(
            title='Тестовый курс для Celery',
            description='Этот курс создан для тестирования отправки email уведомлений через Celery.',
            owner=user,  # Обязательное поле
            price=0.00,  # Обязательное поле (есть default, но лучше явно указать)
            preview=None,  # Необязательное поле
            stripe_product_id=None,
            stripe_price_id=None
        )
        print(f"✅ Тестовый курс создан: {course.title}")

    # 3. СОЗДАНИЕ/ПОИСК ПОДПИСКИ
    subscription, created = Subscription.objects.get_or_create(
        user=user,
        course=course,
        defaults={'is_active': True}
    )
    status = 'создана' if created else 'найдена'
    print(f"✅ Подписка {status}: {user.email} -> {course.title}")

    # 4. ДОПОЛНИТЕЛЬНО: создание тестового урока (опционально, для полного теста)
    try:
        lesson = Lesson.objects.get(
            title='Тестовый урок для Celery',
            owner=user,
            course=course
        )
        print(f"✅ Тестовый урок найден: {lesson.title}")
    except Lesson.DoesNotExist:
        lesson = Lesson.objects.create(
            title='Тестовый урок для Celery',
            description='Этот урок создан для тестирования.',
            course=course,
            owner=user,
            price=0.00,
            video_url='https://www.youtube.com/watch?v=dQw4w9WgXcQ',  # Заглушка
            preview=None,
            stripe_product_id=None,
            stripe_price_id=None
        )
        print(f"✅ Тестовый урок создан: {lesson.title}")

    print("=" * 60)
    print("✅ ВСЁ ГОТОВО! Тестовые данные созданы:")
    print(f"   👤 Пользователь: {user.email}")
    print(f"   📚 Курс: {course.title} (ID: {course.id})")
    print(f"   🔔 Подписка: {'активна' if subscription.is_active else 'неактивна'}")
    print(f"   📖 Урок: {lesson.title}")
    print("=" * 60)
    print("🎯 Дальнейшие действия:")
    print("1. Убедитесь, что работают Redis и PostgreSQL")
    print("2. Запустите Celery Worker в одном терминале:")
    print("   celery -A config worker --pool=solo -l info")
    print("3. Запустите Celery Beat в другом терминале:")
    print("   celery -A config beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler")
    print("4. Обновите курс через админку Django или ваш API")
    print("5. Проверьте логи Celery Worker на наличие задачи send_course_update_email")
    print("=" * 60)

    # Возвращаем объекты для возможного использования
    return {
        'user': user,
        'course': course,
        'subscription': subscription,
        'lesson': lesson
    }


def cleanup_test_data():
    """
    Очищает тестовые данные (опционально).
    """
    print("=" * 60)
    print("Очистка тестовых данных...")
    print("=" * 60)

    deleted_count = 0

    try:
        user = User.objects.get(email='celery_test@example.com')
        # Удаляем связанные объекты (курс, уроки, подписки)
        user_courses = Course.objects.filter(owner=user)
        user_lessons = Lesson.objects.filter(owner=user)
        user_subscriptions = Subscription.objects.filter(user=user)

        user_subscriptions.delete()
        user_lessons.delete()
        user_courses.delete()
        user.delete()

        deleted_count += 1
        print("✅ Тестовый пользователь и все связанные данные удалены")
    except User.DoesNotExist:
        print("ℹ️ Тестовый пользователь не найден")

    print(f"✅ Удалено объектов: {deleted_count}")
    print("=" * 60)
    print("Очистка завершена!")
    print("=" * 60)


if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == '--cleanup':
        cleanup_test_data()
    else:
        create_test_data()