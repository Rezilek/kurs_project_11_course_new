# users/models.py
from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _
from django.conf import settings


class UserManager(BaseUserManager):
    """Define a model manager for User model with no username field."""

    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        """Create and save a User with the given email and password."""
        if not email:
            raise ValueError('The given email must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        """Create and save a regular User with the given email and password."""
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        """Create and save a SuperUser with the given email and password."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    username = None
    email = models.EmailField(_('email address'), unique=True)
    phone = models.CharField(max_length=15, blank=True, null=True, verbose_name='Телефон')
    city = models.CharField(max_length=100, blank=True, null=True, verbose_name='Город')
    avatar = models.ImageField(upload_to='users/avatars/', blank=True, null=True, verbose_name='Аватарка')

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserManager()

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ['email']

    def __str__(self):
        return self.email


class Payment(models.Model):
    PAYMENT_METHOD_CHOICES = [
        ('cash', 'Наличные'),
        ('transfer', 'Перевод на счет'),
        ('stripe', 'Stripe'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Ожидает оплаты'),
        ('paid', 'Оплачено'),
        ('cancelled', 'Отменено'),
        ('failed', 'Неудачно'),
    ]

    CURRENCY_CHOICES = [
        ('usd', 'USD'),
        ('eur', 'EUR'),
        ('rub', 'RUB'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name='Пользователь')
    paid_course = models.ForeignKey('courses.Course', on_delete=models.CASCADE, verbose_name='Оплаченный курс',
                                    null=True, blank=True)
    paid_lesson = models.ForeignKey('courses.Lesson', on_delete=models.CASCADE, verbose_name='Оплаченный урок',
                                    null=True, blank=True)

    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Сумма оплаты')
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='usd', verbose_name='Валюта')

    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='stripe',
                                      verbose_name='Способ оплаты')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='Статус платежа')

    # Stripe fields
    stripe_session_id = models.CharField(max_length=255, blank=True, verbose_name='ID сессии Stripe')
    stripe_payment_intent_id = models.CharField(max_length=255, blank=True, verbose_name='ID платежа Stripe')
    stripe_customer_id = models.CharField(max_length=255, blank=True, verbose_name='ID клиента Stripe')

    stripe_metadata = models.JSONField(default=dict, blank=True, verbose_name='Метаданные Stripe')

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')
    stripe_product_id = models.CharField(max_length=255, blank=True, verbose_name='ID продукта Stripe')
    stripe_price_id = models.CharField(max_length=255, blank=True, verbose_name='ID цены Stripe')
    payment_url = models.URLField(max_length=500, blank=True, verbose_name='Ссылка на оплату')

    def clean(self):
        """Валидация: платеж должен быть либо за курс, либо за урок"""
        from django.core.exceptions import ValidationError

        if not self.paid_course and not self.paid_lesson:
            raise ValidationError('Платеж должен быть связан с курсом или уроком')
        if self.paid_course and self.paid_lesson:
            raise ValidationError('Платеж может быть связан только с курсом ИЛИ уроком, не с обоими')

        super().clean()

    class Meta:
        verbose_name = 'Платеж'
        verbose_name_plural = 'Платежи'
        ordering = ['-created_at']


    def __str__(self):
        item = self.paid_course.title if self.paid_course else self.paid_lesson.title
        return f"Платеж {self.id} - {self.user.email} - {self.amount} {self.currency} - {item}"