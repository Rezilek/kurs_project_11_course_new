from django.contrib.auth.models import User
from django.db import models
from django.conf import settings
from .validators import validate_youtube_url


class Course(models.Model):
    title = models.CharField(max_length=255, verbose_name='Название')
    description = models.TextField(verbose_name='Описание')
    preview = models.ImageField(upload_to='courses/previews/', null=True, blank=True, verbose_name='Превью')
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                              related_name='courses', null=True, blank=True, verbose_name='Владелец')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')

    class Meta:
        verbose_name = 'Курс'
        verbose_name_plural = 'Курсы'
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class Lesson(models.Model):
    title = models.CharField(max_length=255, verbose_name='Название')
    description = models.TextField(verbose_name='Описание')
    preview = models.ImageField(
        upload_to='lessons/previews/',
        verbose_name='Превью',
        blank=True,
        null=True
    )
    video_url = models.URLField(
        verbose_name='Ссылка на видео',
        blank=True,
        null=True,
        validators=[validate_youtube_url]  # Добавляем валидатор
    )
    course = models.ForeignKey(
        'Course',
        on_delete=models.CASCADE,
        related_name='lessons',
        verbose_name='Курс'
    )
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='lessons',
        verbose_name='Владелец'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')

    class Meta:
        verbose_name = 'Урок'
        verbose_name_plural = 'Уроки'
        ordering = ['created_at']

    def __str__(self):
        return self.title

    def clean(self):
        """Валидация модели перед сохранением"""
        from .validators import validate_no_external_links

        # Проверяем описание на внешние ссылки
        if self.description:
            validate_no_external_links(self.description)

        super().clean()


class Subscription(models.Model):
    """Модель подписки пользователя на курс"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='subscriptions',
        verbose_name='пользователь'
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='subscriptions',
        verbose_name='курс'
    )
    is_active = models.BooleanField(default=True, verbose_name='активна')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')

    class Meta:
        verbose_name = 'подписка'
        verbose_name_plural = 'подписки'
        unique_together = ['user', 'course']

    def __str__(self):
        return f"{self.user.email} - {self.course.title}"
    