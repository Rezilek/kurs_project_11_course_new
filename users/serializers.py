from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from .models import Payment

User = get_user_model()


class PaymentDetailSerializer(serializers.ModelSerializer):
    """Детальный сериализатор для платежа с информацией о пользователе и курсе/уроке"""
    user_email = serializers.EmailField(source='user.email', read_only=True)
    item_title = serializers.SerializerMethodField(read_only=True)
    item_type = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Payment
        fields = [
            'id', 'user', 'user_email', 'paid_course', 'paid_lesson',
            'item_title', 'item_type', 'amount', 'currency',
            'payment_method', 'status', 'stripe_session_id',
            'stripe_payment_intent_id', 'payment_url',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'user', 'user_email', 'item_title', 'item_type',
            'stripe_session_id', 'stripe_payment_intent_id', 'payment_url',
            'created_at', 'updated_at'
        ]

    def get_item_title(self, obj):
        if obj.paid_course:
            return obj.paid_course.title
        elif obj.paid_lesson:
            return obj.paid_lesson.title
        return None

    def get_item_type(self, obj):
        if obj.paid_course:
            return 'course'
        elif obj.paid_lesson:
            return 'lesson'
        return None


class PaymentSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)
    item_title = serializers.SerializerMethodField(read_only=True)
    item_type = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Payment
        fields = [
            'id', 'user', 'user_email', 'paid_course', 'paid_lesson',
            'item_title', 'item_type', 'amount', 'currency',
            'payment_method', 'status', 'stripe_session_id',
            'payment_url', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'user', 'user_email', 'item_title', 'item_type',
            'stripe_session_id', 'payment_url', 'created_at', 'updated_at'
        ]

    @extend_schema_field(str)
    def get_item_title(self, obj):
        """Получить название оплаченного элемента"""
        if obj.paid_course:
            return str(obj.paid_course)
        elif obj.paid_lesson:
            return str(obj.paid_lesson)
        return "Не указано"

    @extend_schema_field(str)
    def get_item_type(self, obj):
        """Получить тип оплаченного элемента"""
        if obj.paid_course:
            return "course"
        elif obj.paid_lesson:
            return "lesson"
        return "unknown"


class PaymentCreateSerializer(serializers.Serializer):
    """Сериализатор для создания платежа через Stripe"""
    item_type = serializers.ChoiceField(choices=['course', 'lesson'])
    item_id = serializers.IntegerField()
    success_url = serializers.URLField(
        required=False,
        default='http://localhost:8000/api/users/payments/success/'
    )
    cancel_url = serializers.URLField(
        required=False,
        default='http://localhost:8000/api/users/payments/cancel/'
    )

    def validate_item_id(self, value):
        from courses.models import Course, Lesson

        item_type = self.initial_data.get('item_type')

        if item_type == 'course':
            if not Course.objects.filter(id=value).exists():
                raise serializers.ValidationError(f"Курс с ID {value} не найден")
        elif item_type == 'lesson':
            if not Lesson.objects.filter(id=value).exists():
                raise serializers.ValidationError(f"Урок с ID {value} не найден")

        return value


class PublicUserSerializer(serializers.ModelSerializer):
    """Сериализатор для публичного просмотра профилей"""

    class Meta:
        model = User
        fields = ('id', 'email', 'first_name', 'city', 'avatar')
        read_only_fields = ('id', 'email', 'first_name', 'city', 'avatar')


class PrivateUserSerializer(serializers.ModelSerializer):
    """Сериализатор для просмотра своего профиля с историей платежей"""
    payment_history = PaymentDetailSerializer(source='payments', many=True, read_only=True)

    class Meta:
        model = User
        fields = ('id', 'email', 'first_name', 'last_name',
                  'phone', 'city', 'avatar', 'payment_history')
        read_only_fields = ('id', 'email', 'payment_history')


class UserRegisterSerializer(serializers.ModelSerializer):
    """Сериализатор для регистрации пользователей"""
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ('id', 'email', 'password', 'password2',
                  'first_name', 'last_name', 'phone', 'city', 'avatar')

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Пароли не совпадают"})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        return User.objects.create_user(**validated_data)


class UserSerializer(serializers.ModelSerializer):
    """Основной сериализатор пользователя с логикой выбора подходящего"""

    class Meta:
        model = User
        fields = '__all__'
        read_only_fields = ('id', 'last_login', 'is_superuser',
                            'is_staff', 'is_active', 'date_joined',
                            'groups', 'user_permissions')

    def to_representation(self, instance):
        """Динамический выбор сериализатора в зависимости от контекста"""
        request = self.context.get('request')

        if request and request.user == instance:
            # Для своего профиля используем приватный сериализатор
            return PrivateUserSerializer(instance, context=self.context).data
        else:
            # Для чужого профиля используем публичный сериализатор
            return PublicUserSerializer(instance, context=self.context).data
