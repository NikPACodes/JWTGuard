from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.auth.password_validation import validate_password

User = get_user_model()

class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True, min_length=8)
    role = serializers.CharField(max_length=150)

    def validate_email(self, value):
        email = value.lower().strip()
        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError('Email уже зарегистрирован.')
        return email

    def validate_username(self, value):
        value = value.strip()
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError('Пользователь с таким ником уже существует.')
        return value

    def validate_role(self, value):
        value = value.strip()
        if not Group.objects.filter(name=value).exists():
            raise serializers.ValidationError("Указанная роль не существует.")
        return value

    def validate_password(self, value):
        user = User(
            email = self.initial_data.get('email'),
            username = self.initial_data.get('username'),
        )
        validate_password(password=value, user=user)
        return value


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class RefreshSerializer(serializers.Serializer):
    refresh = serializers.CharField()


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()