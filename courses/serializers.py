# courses/serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from .models import Course, Lesson, Subscription
from .validators import validate_youtube_url, validate_no_external_links
from drf_spectacular.utils import extend_schema_field
from drf_spectacular.types import OpenApiTypes

User = get_user_model()


class LessonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')

    def validate_video_url(self, value):
        """Валидация видео ссылки в сериализаторе"""
        if value:
            try:
                validate_youtube_url(value)
            except ValidationError as e:
                raise serializers.ValidationError(e.message)
        return value

    def validate_description(self, value):
        """Валидация описания на внешние ссылки"""
        if value:
            try:
                validate_no_external_links(value)
            except ValidationError as e:
                raise serializers.ValidationError(e.message)
        return value

    def validate(self, data):
        """Общая валидация данных урока"""
        return data


class CourseSerializer(serializers.ModelSerializer):
    lessons_count = serializers.IntegerField(source='lessons.count', read_only=True)
    lessons = LessonSerializer(many=True, read_only=True)
    owner = serializers.HiddenField(default=serializers.CurrentUserDefault())
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = '__all__'

    def validate_description(self, value):
        """Валидация описания курса на внешние ссылки"""
        if value:
            try:
                validate_no_external_links(value)
            except ValidationError as e:
                raise serializers.ValidationError(e.message)
        return value

    @extend_schema_field(OpenApiTypes.BOOL)
    def get_is_subscribed(self, obj):
        """Определяет, подписан ли текущий пользователь на курс"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Subscription.objects.filter(
                user=request.user,
                course=obj,
                is_active=True
            ).exists()
        return False


class SubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscription
        fields = '__all__'
        read_only_fields = ['user']

    def create(self, validated_data):
        """Автоматически устанавливаем текущего пользователя"""
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class PaymentSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Payment из users.models"""

    # Импортируем Payment ТОЛЬКО внутри класса
    def __init__(self, *args, **kwargs):
        from users.models import Payment
        self.Meta.model = Payment
        super().__init__(*args, **kwargs)

    course_title = serializers.SerializerMethodField()
    lesson_title = serializers.SerializerMethodField()
    user_email = serializers.SerializerMethodField()

    class Meta:
        # Model будет установлен в __init__
        fields = [
            'id', 'user', 'user_email',
            'paid_course', 'course_title',
            'paid_lesson', 'lesson_title',
            'amount', 'currency', 'payment_method', 'status',
            'stripe_session_id', 'stripe_payment_intent_id', 'stripe_customer_id',
            'stripe_metadata', 'created_at', 'updated_at'
        ]

    def get_course_title(self, obj):
        return obj.paid_course.title if obj.paid_course else None

    def get_lesson_title(self, obj):
        return obj.paid_lesson.title if obj.paid_lesson else None

    def get_user_email(self, obj):
        return obj.user.email if obj.user else None


class PaymentCreateSerializer(serializers.Serializer):
    """
    Сериализатор для создания платежа
    """
    course_id = serializers.IntegerField(required=False)
    lesson_id = serializers.IntegerField(required=False)
    payment_method = serializers.ChoiceField(
        choices=['cash', 'transfer', 'stripe'],
        default='stripe'
    )

    def validate(self, data):
        """
        Проверяет, что указан либо курс, либо урок
        """
        course_id = data.get('course_id')
        lesson_id = data.get('lesson_id')

        if not course_id and not lesson_id:
            raise serializers.ValidationError("Укажите course_id или lesson_id")

        if course_id and lesson_id:
            raise serializers.ValidationError("Укажите только course_id ИЛИ lesson_id")

        return data

    def validate_course_id(self, value):
        if not Course.objects.filter(id=value).exists():
            raise serializers.ValidationError("Курс с указанным ID не существует")
        return value

    def validate_lesson_id(self, value):
        if not Lesson.objects.filter(id=value).exists():
            raise serializers.ValidationError("Урок с указанным ID не существует")
        return value