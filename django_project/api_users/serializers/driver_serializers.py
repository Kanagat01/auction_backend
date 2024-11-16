from rest_framework import serializers
from api_users.models import PhoneNumberChangeRequest, PhoneNumberValidator, UserModel, DriverProfile, DriverAuthRequest


class DriverAuthRequestSerializer(serializers.Serializer):
    phone_number = serializers.CharField(
        max_length=17, validators=[PhoneNumberValidator()])


class DriverAuthConfirmSerializer(serializers.Serializer):
    phone_number = serializers.CharField(
        max_length=17, validators=[PhoneNumberValidator()])
    confirmation_code = serializers.CharField(max_length=4)

    def validate(self, attrs):
        phone_number = attrs.get('phone_number')
        confirmation_code = attrs.get('confirmation_code')

        if len(confirmation_code) != 4 or not confirmation_code.isdigit():
            raise serializers.ValidationError("invalid_confirmation_code")

        try:
            driver_register_request = DriverAuthRequest.objects.get(
                phone_number=phone_number)
            if driver_register_request.confirmation_code != confirmation_code:
                raise serializers.ValidationError("wrong_code")

            attrs['driver_register_request'] = driver_register_request
            return attrs

        except DriverAuthRequest.DoesNotExist:
            raise serializers.ValidationError(
                "driver_register_request_does_not_exist")


class SetDriverProfileDataSerializer(serializers.ModelSerializer):
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
        exclude = ['user', 'phone_number']

    def __init__(self, user: UserModel, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    def validate_machine_number(self, value):
        if DriverProfile.objects.exclude(user=self.user).filter(machine_number=value).exists():
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

    def __init__(self, driver: DriverProfile, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.driver: DriverProfile = driver

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
