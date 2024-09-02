from datetime import datetime
from rest_framework import serializers
from api_users.models import PhoneNumberChangeRequest, PhoneNumberValidator, DriverProfile, DriverRegisterRequest
from .authentication_serializers import PasswordResetConfirmSerializer


class RegisterDriverRequestSerializer(serializers.Serializer):
    phone_number = serializers.CharField(
        max_length=17, validators=[PhoneNumberValidator()])


class RegisterDriverConfirmSerializer(serializers.Serializer):
    phone_number = serializers.CharField(
        max_length=17, validators=[PhoneNumberValidator()])
    confirmation_code = serializers.CharField(max_length=4)

    def validate(self, attrs):
        phone_number = attrs.get('phone_number')
        confirmation_code = attrs.get('confirmation_code')

        if len(confirmation_code) != 4 or not confirmation_code.isdigit():
            raise serializers.ValidationError("invalid_confirmation_code")

        try:
            driver_register_request = DriverRegisterRequest.objects.get(
                phone_number=phone_number)
            if driver_register_request.confirmation_code != confirmation_code:
                raise serializers.ValidationError("wrong_code")

            attrs['driver_register_request'] = driver_register_request
            return attrs

        except DriverRegisterRequest.DoesNotExist:
            raise serializers.ValidationError(
                "driver_register_request_does_not_exist")


class SetDriverPasswordAndBirthDate(PasswordResetConfirmSerializer):
    birth_date = serializers.DateField(required=False)

    def to_internal_value(self, data):
        try:
            return super().to_internal_value(data)
        except serializers.ValidationError:
            pass

        try:
            data['birth_date'] = datetime.strptime(
                data['birth_date'], '%d.%m.%Y').date()
        except (ValueError, TypeError):
            raise serializers.ValidationError(
                {'birth_date': 'Invalid date format. Try: YYYY-MM-DD'})
        return super().to_internal_value(data)


class SetDriverProfileDataSerializer(SetDriverPasswordAndBirthDate, serializers.ModelSerializer):
    full_name = serializers.CharField(
        max_length=300,
        error_messages={
            'required': 'required',
            'max_length': 'max_length is 300 symbols'
        }
    )
    machine_number = serializers.CharField(
        max_length=20,
        error_messages={
            'required': 'required',
            'max_length': 'max_length is 20 symbols'
        }
    )

    class Meta:
        model = DriverProfile
        exclude = ['user']

    def validate_machine_number(self, value):
        if DriverProfile.objects.filter(machine_number=value).exists():
            raise serializers.ValidationError("must_be_unique")
        return value


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
