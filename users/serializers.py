from rest_framework import serializers
from .models import User, Payment


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = '__all__'
        read_only_fields = ['payment_date']


class UserSerializer(serializers.ModelSerializer):
    payment_history = PaymentSerializer(
        source='payments',  # используем related_name из модели
        many=True,
        read_only=True
    )

    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name',
            'phone', 'city', 'avatar', 'payment_history'
        ]