# courses/models.py - ОБНОВЛЕННЫЕ модели
from django.db import models
from django.conf import settings


class Course(models.Model):
    """Модель курса"""
    title = models.CharField(max_length=255, verbose_name="Название")
    description = models.TextField(verbose_name="Описание")
    preview = models.ImageField(
        upload_to='courses/previews/',
        verbose_name="Превью",
        null=True,
        blank=True
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name="Владелец"
    )

    # Поле цены для Stripe интеграции
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        verbose_name="Цена курса",
        help_text="Цена в рублях"
    )

    # ПОЛЯ ДЛЯ STRIPE
    stripe_product_id = models.CharField(
        max_length=255,
        verbose_name="ID продукта Stripe",
        blank=True,
        null=True,
        help_text="Автоматически создается при первой оплате"
    )
    stripe_price_id = models.CharField(
        max_length=255,
        verbose_name="ID цены Stripe",
        blank=True,
        null=True,
        help_text="Автоматически создается при первой оплате"
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    class Meta:
        verbose_name = "Курс"
        verbose_name_plural = "Курсы"
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class Lesson(models.Model):
    """Модель урока"""
    title = models.CharField(max_length=255, verbose_name="Название")
    description = models.TextField(verbose_name="Описание")
    preview = models.ImageField(
        upload_to='lessons/previews/',
        verbose_name="Превью",
        null=True,
        blank=True
    )
    video_url = models.URLField(
        verbose_name="Ссылка на видео",
        help_text="Только YouTube ссылки"
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        verbose_name="Курс",
        related_name='lessons'
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name="Владелец"
    )

    # Цена урока - ДОБАВЬТЕ ЕСЛИ НЕТ
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        verbose_name="Цена урока",
        help_text="Цена в рублях"
    )

    # ПОЛЯ ДЛЯ STRIPE
    stripe_product_id = models.CharField(
        max_length=255,
        verbose_name="ID продукта Stripe",
        blank=True,
        null=True,
        help_text="Автоматически создается при первой оплате"
    )
    stripe_price_id = models.CharField(
        max_length=255,
        verbose_name="ID цены Stripe",
        blank=True,
        null=True,
        help_text="Автоматически создается при первой оплате"
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    class Meta:
        verbose_name = "Урок"
        verbose_name_plural = "Уроки"
        ordering = ['created_at']

    def __str__(self):
        return self.title


class Subscription(models.Model):
    """Модель подписки на курс"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name="Пользователь"
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        verbose_name="Курс"
    )
    is_active = models.BooleanField(default=True, verbose_name="Активна")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    class Meta:
        verbose_name = "Подписка"
        verbose_name_plural = "Подписки"
        unique_together = ['user', 'course']
        ordering = ['-created_at']

    def __str__(self):
        status = "активна" if self.is_active else "неактивна"
        return f"{self.user.email} -> {self.course.title} ({status})"
