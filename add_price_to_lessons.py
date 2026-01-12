import os
import django
import sys

sys.path.append('/path/to/your/project')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from courses.models import Lesson

def add_default_price_to_lessons():
    """Добавляет цену по умолчанию для уроков"""
    lessons = Lesson.objects.filter(price=0)
    for lesson in lessons:
        lesson.price = 500.00  # Примерная цена
        lesson.save()
        print(f"Добавлена цена для урока: {lesson.title}")

if __name__ == '__main__':
    add_default_price_to_lessons()