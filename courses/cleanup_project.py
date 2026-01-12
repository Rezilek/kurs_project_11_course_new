import os
import shutil

print("=" * 70)
print("ОЧИСТКА ПРОЕКТА ОТ ПОВРЕЖДЕННЫХ ФАЙЛОВ")
print("=" * 70)

# 1. Удаляем старые файлы
files_to_remove = [
    'courses/models_backup.py',
    'courses/serializers_backup.py',
    'courses/serializers_backup2.py',
]

for file in files_to_remove:
    if os.path.exists(file):
        os.remove(file)
        print(f"✅ Удален: {file}")
    else:
        print(f"⚠️ Не найден: {file}")

# 2. Проверяем курсовые миграции
print("\n2. 🔍 Проверка миграций courses...")
migrations_dir = 'courses/migrations'
if os.path.exists(migrations_dir):
    for file in os.listdir(migrations_dir):
        if file.endswith('.py') and 'payment' in file.lower():
            filepath = os.path.join(migrations_dir, file)
            os.remove(filepath)
            print(f"✅ Удалена миграция: {file}")

# 3. Проверяем users миграции
print("\n3. 🔍 Проверка миграций users...")
migrations_dir = 'users/migrations'
if os.path.exists(migrations_dir):
    for file in os.listdir(migrations_dir):
        if file.endswith('.py') and file != '__init__.py':
            filepath = os.path.join(migrations_dir, file)
            print(f"   Найдена: {file}")

print("\n" + "=" * 70)
print("РЕКОМЕНДАЦИИ:")
print("=" * 70)
print("1. Создайте новые миграции:")
print("   python manage.py makemigrations")
print("2. Примените миграции:")
print("   python manage.py migrate")
print("3. Перезапустите сервер:")
print("   python manage.py runserver")