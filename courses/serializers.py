# -*- coding: utf-8 -*-
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from users.models import Payment
from courses.models import Course, Lesson, Subscription
from .validators import validate_youtube_url, validate_no_external_links

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
        # Дополнительные проверки, если нужно
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