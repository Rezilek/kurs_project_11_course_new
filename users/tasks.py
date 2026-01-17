# users/tasks.py
from celery import shared_task
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

User = get_user_model()


@shared_task
def block_inactive_users():
    """
    Проверяет пользователей по дате последнего входа (last_login)
    и блокирует тех, кто не заходил более месяца
    """
    one_month_ago = timezone.now() - timedelta(days=30)
    inactive_users = User.objects.filter(
        last_login__lt=one_month_ago,
        is_active=True
    )

    count = inactive_users.count()
    inactive_users.update(is_active=False)

    return f"Заблокировано {count} неактивных пользователей"
