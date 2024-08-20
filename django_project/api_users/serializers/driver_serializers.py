from rest_framework import serializers
from api_users.models.profiles import PhoneNumberChangeRequest, PhoneNumberValidator, DriverProfile


class PhoneNumberChangeRequestSerializer(serializers.Serializer):
    new_phone_number = serializers.CharField(
        max_length=17, validators=[PhoneNumberValidator()])

    def validate_new_phone_number(self, value):
        if DriverProfile.objects.filter(phone_number=value).exists():
            raise serializers.ValidationError("phone_number already exists")
        return value


class ConfirmPhoneNumberSerializer(serializers.Serializer):
    confirmation_code = serializers.CharField(max_length=4)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'request' not in self.context:
            raise serializers.ValidationError(
                "Request is required in context. [Contact to developer]")
        if not hasattr(self.context['request'].user, 'driver_profile'):
            raise serializers.ValidationError(
                "Request user must be a Driver. [Contact to developer]")
        self.driver: DriverProfile = self.context['request'].user.driver_profile

    def validate_confirmation_code(self, value: str):
        if len(value) != 4 or not value.isdigit():
            raise serializers.ValidationError("invalid_confirmation_code")
        try:
            phone_change_request = PhoneNumberChangeRequest.objects.get(
                driver=self.driver)
            if phone_change_request.confirmation_code != value:
                raise serializers.ValidationError("wrong_code")
            return phone_change_request
        except PhoneNumberChangeRequest.DoesNotExist:
            raise serializers.ValidationError(
                "phone_change_request_does_not_exist")
