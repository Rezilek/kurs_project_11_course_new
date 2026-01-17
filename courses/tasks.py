# courses/tasks.py
from celery import shared_task
from django.core.mail import send_mail
from django.utils import timezone
from django.conf import settings
from django.contrib.auth import get_user_model
from .models import Course, Subscription
from datetime import timedelta

User = get_user_model()


@shared_task
def send_course_update_email(course_id, update_message):
    """
    Отправляет email пользователям об обновлении курса
    """
    try:
        course = Course.objects.get(id=course_id)
        subscribers = Subscription.objects.filter(
            course=course,
            is_active=True
        ).select_related('user')

        for subscription in subscribers:
            subject = f'Обновление курса: {course.title}'
            message = f'''
            Здравствуйте, {subscription.user.username}!

            Курс "{course.title}" был обновлен.

            {update_message}

            С уважением,
            Команда обучающей платформы
            '''

            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[subscription.user.email],
                fail_silently=False,
            )

        return f"Письма отправлены {subscribers.count()} подписчикам курса {course.title}"

    except Course.DoesNotExist:
        return f"Курс с id {course_id} не найден"


@shared_task
def check_inactive_users():
    """
    Проверяет пользователей, которые не заходили более месяца,
    и блокирует их (устанавливает is_active=False)
    """
    one_month_ago = timezone.now() - timedelta(days=30)
    inactive_users = User.objects.filter(
        last_login__lt=one_month_ago,
        is_active=True
    )

    count = inactive_users.count()
    inactive_users.update(is_active=False)

    return f"Заблокировано {count} неактивных пользователей"
