import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from courses.models import Lesson, Course
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model

User = get_user_model()

print("=== ПРОВЕРКА ВАЛИДАТОРОВ ===")

# 1. Проверяем поле video_url
field = Lesson._meta.get_field('video_url')
print(f"1. Поле video_url имеет валидаторов: {len(field.validators)}")
for i, validator in enumerate(field.validators, 1):
    print(f"   {i}. {validator.__class__.__name__}: {validator}")

# 2. Получаем существующего пользователя или создаем нового
try:
    user = User.objects.get(email='test@example.com')
    print(f"\n2. Используем существующего пользователя: {user.email}")
except User.DoesNotExist:
    try:
        user = User.objects.create_user(email='test2@example.com', password='testpass')
        print(f"\n2. Создан новый пользователь: {user.email}")
    except:
        # Если и это не получается, берем первого пользователя
        user = User.objects.first()
        print(f"\n2. Используем первого пользователя: {user.email}")

# 3. Создаем курс
course, created = Course.objects.get_or_create(
    title='Тестовый курс для валидации',
    defaults={
        'description': 'Описание тестового курса',
        'owner': user
    }
)
print(f"3. Курс: {'создан' if created else 'уже существует'}")

print("\n4. Тест невалидной ссылки (vimeo.com):")
lesson1 = Lesson(
    title='Тест невалидной ссылки',
    description='Простое описание',
    video_url='https://vimeo.com/123456',  # Не YouTube!
    course=course,
    owner=user
)

try:
    lesson1.full_clean()
    print("   ❌ ОШИБКА: full_clean() НЕ вызвал ValidationError!")
    print("   Причина: валидатор validate_youtube_url не подключен к полю video_url")
    print("   Исправьте в models.py: validators=[validate_youtube_url]")
except ValidationError as e:
    print(f"   ✅ УСПЕХ: full_clean() вызвал ValidationError")
    print(f"   Ошибки: {e.message_dict}")

print("\n5. Тест валидной ссылки (youtube.com):")
lesson2 = Lesson(
    title='Тест валидной ссылки',
    description='Простое описание',
    video_url='https://youtube.com/watch?v=abc123',  # YouTube!
    course=course,
    owner=user
)

try:
    lesson2.full_clean()
    print("   ✅ УСПЕХ: Валидная ссылка принята")
except ValidationError as e:
    print(f"   ❌ ОШИБКА: Валидная ссылка отвергнута: {e}")

print("\n6. Проверка метода clean() на внешние ссылки:")
lesson3 = Lesson(
    title='Тест внешних ссылок',
    description='Ссылка на Vimeo: https://vimeo.com/123',
    video_url='https://youtube.com/watch?v=abc123',
    course=course,
    owner=user
)

try:
    lesson3.full_clean()
    print("   ❌ ОШИБКА: Метод clean() не обнаружил внешние ссылки")
except ValidationError as e:
    print(f"   ✅ УСПЕХ: Обнаружены внешние ссылки")
    print(f"   Ошибка: {e}")

print("\n7. Проверка импорта валидаторов:")
try:
    from courses.validators import validate_youtube_url, validate_no_external_links
    print("   ✅ Валидаторы успешно импортированы")
    
    # Проверяем работу валидаторов напрямую
    print("\n8. Прямая проверка валидаторов:")
    try:
        validate_youtube_url('https://vimeo.com/123')
        print("   ❌ validate_youtube_url принял vimeo.com")
    except ValidationError:
        print("   ✅ validate_youtube_url отклонил vimeo.com")
    
    try:
        validate_youtube_url('https://youtube.com/watch?v=abc')
        print("   ✅ validate_youtube_url принял youtube.com")
    except ValidationError:
        print("   ❌ validate_youtube_url отклонил youtube.com")
        
except ImportError as e:
    print(f"   ❌ ОШИБКА импорта: {e}")
    print("   Убедитесь, что файл courses/validators.py существует")
