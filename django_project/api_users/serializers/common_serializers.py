from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from api_users.models import UserModel


class RegisterManagerSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(max_length=200)
    full_name = serializers.CharField(max_length=200)

    def validate_email(self, email):
        if UserModel.objects.filter(email=email).exists():
            raise serializers.ValidationError('user_already_exists')
        return email

    def validate_password(self, password):
        validate_password(password)
        return password


class EditUserSerializer(serializers.Serializer):
    email = serializers.EmailField()
    full_name = serializers.CharField(max_length=200)
    company_name = serializers.CharField(max_length=200)
    details = serializers.CharField(
        required=False, allow_blank=True, allow_null=True)

    def __init__(self, *args, from_manager=False, **kwargs):
        super().__init__(*args, **kwargs)
        if from_manager:
            self.fields.pop('company_name')
            self.fields.pop('details')


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(max_length=200)
    new_password = serializers.CharField(max_length=200)
    repeat_password = serializers.CharField(max_length=200)
