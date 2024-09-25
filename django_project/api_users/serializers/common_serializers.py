from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from api_users.models import *


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


class EditManagerSerializer(serializers.Serializer):
    manager_id = serializers.IntegerField()
    email = serializers.EmailField()
    full_name = serializers.CharField(max_length=200)

    def __init__(self, user: UserModel, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if hasattr(user, 'customer_company'):
            self.company: CustomerCompany = user.customer_company
        elif hasattr(user, "transporter_company"):
            self.company: TransporterCompany = user.transporter_company
        else:
            raise serializers.ValidationError(
                "Request user must be a CustomerCompany or TransporterCompany. [Contact to developer]")

    def validate_manager_id(self, manager_id):
        try:
            manager = self.company.managers.get(id=manager_id)
            return manager
        except [CustomerManager.DoesNotExist, TransporterManager.DoesNotExist]:
            raise serializers.ValidationError(
                "Manager with this id does not exist or does not belong to you")


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


class ChangeSubscriptionSerializer(serializers.Serializer):
    subscription_id = serializers.IntegerField()

    def validate_subscription_id(self, value):
        user_type = self.context['user_type']
        try:
            if user_type == UserTypes.CUSTOMER_COMPANY:
                subscription = CustomerSubscription.objects.get(id=value)
            elif user_type == UserTypes.TRANSPORTER_COMPANY:
                subscription = TransporterSubscription.objects.get(id=value)
            else:
                raise serializers.ValidationError(
                    "Only company accounts can change subscription")
        except [CustomerSubscription.DoesNotExist, TransporterSubscription.DoesNotExist]:
            raise serializers.ValidationError("subscription does not exist")
        return subscription
