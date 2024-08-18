from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from api_users.models import UserModel


class PasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    new_password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)


class LogInSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=200)
    password = serializers.CharField(max_length=200)


class RegisterCompanySerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(max_length=200)
    full_name = serializers.CharField(max_length=200)
    company_name = serializers.CharField(max_length=200)

    def validate_email(self, email):
        if UserModel.objects.filter(email=email).exists():
            raise serializers.ValidationError('user_already_exists')
        return email

    def validate_password(self, password):
        validate_password(password)
        return password
