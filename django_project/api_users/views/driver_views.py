from smsaero import SmsAeroException
from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.authtoken.models import Token
from api_users.permissions import IsDriverAccount
from api_users.serializers import DriverProfileSerializer
from api_users.serializers.driver_serializers import *
from api_users.models import UserModel, UserTypes, PhoneNumberChangeRequest, DriverProfile, DriverAuthRequest
from backend.global_functions import send_sms, success_with_text, error_with_text


class DriverAuthRequestView(APIView):
    '''Ендпоинт для авторизации водителя'''
    permission_classes = ()

    def post(self, request: Request):
        # print(request.data)
        serializer = DriverAuthRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return error_with_text(serializer.errors)

        phone_number = serializer.validated_data['phone_number']
        try:
            driver_register_request = DriverAuthRequest.objects.get(
                phone_number=phone_number)
        except DriverAuthRequest.DoesNotExist:
            driver_register_request = DriverAuthRequest.objects.create(
                phone_number=phone_number)

        driver_register_request.generate_code()
        # print(driver_register_request.confirmation_code)

        try:
            result = send_sms(
                int(phone_number), f"Ваш код подтверждения в Cargonika: {driver_register_request.confirmation_code}")
            return success_with_text(result)
        except SmsAeroException as e:
            print(e)
            return error_with_text('sms_service_error: ' + str(e))


class DriverAuthConfirm(APIView):
    '''Ендпоинт для подтверждения авторизации водителя'''
    permission_classes = ()

    def post(self, request: Request):
        # print(request.data)
        serializer = DriverAuthConfirmSerializer(data=request.data)
        if not serializer.is_valid():
            return error_with_text(serializer.errors)

        driver_register_request: DriverAuthRequest = serializer.validated_data[
            'driver_register_request']

        phone_number = driver_register_request.phone_number
        try:
            driver = DriverProfile.objects.get(phone_number=phone_number)
            user = driver.user
            driver_exist = True

        except DriverProfile.DoesNotExist:
            if UserModel.objects.filter(username=phone_number).exists():
                user = UserModel.objects.get(username=phone_number)
            else:
                user = UserModel.objects.create_user(
                    full_name='',
                    username=phone_number,
                    user_type=UserTypes.DRIVER,
                )
            driver_exist = False

        driver_register_request.delete()
        Token.objects.filter(user=user).delete()
        token = Token.objects.create(user=user)
        return success_with_text({'token': token.key, "driver_exist": driver_exist})


class SetDriverProfileData(APIView):
    '''Ендпоинт для изменения данных водителя'''
    permission_classes = [IsDriverAccount]

    def post(self, request: Request):
        user: UserModel = request.user
        full_name = request.data.get("full_name")

        if not hasattr(user, 'driver_profile'):
            serializer = SetDriverProfileDataSerializer(
                user=user, data=request.data)
            if not serializer.is_valid():
                return error_with_text(serializer.errors)

            DriverProfile.objects.create(
                user=user, **serializer.validated_data)
        else:
            serializer = SetDriverProfileDataSerializer(
                instance=user.driver_profile, user=user, data=request.data, partial=True
            )
            if not serializer.is_valid():
                return error_with_text(serializer.errors)
            serializer.save()

        if full_name:
            user.full_name = full_name
            user.save()
        return success_with_text(DriverProfileSerializer(user.driver_profile).data)


class RequestPhoneNumberChangeView(APIView):
    '''Ендпоинт для изменения номера телефона водителя'''
    permission_classes = [IsDriverAccount]

    def post(self, request: Request):
        serializer = PhoneNumberChangeRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return error_with_text(serializer.errors)

        phone_number = serializer.validated_data['new_phone_number']
        try:
            phone_change_request = PhoneNumberChangeRequest.objects.get(
                driver=request.user.driver_profile)
            phone_change_request.new_phone_number = phone_number
            phone_change_request.save()
        except PhoneNumberChangeRequest.DoesNotExist:
            phone_change_request = PhoneNumberChangeRequest.objects.create(
                driver=request.user.driver_profile, new_phone_number=phone_number)

        phone_change_request.generate_code()

        try:
            result = send_sms(
                int(phone_number), f"Ваш код подтверждения в Cargonika: {phone_change_request.confirmation_code}")
            return success_with_text(result)
        except SmsAeroException as e:
            print(e)
            return error_with_text('sms_service_error: ' + str(e))


class ConfirmPhoneNumberChangeView(APIView):
    '''Ендпоинт для подтверждения изменения телефона водителя'''
    permission_classes = [IsDriverAccount]

    def post(self, request: Request):
        serializer = ConfirmPhoneNumberSerializer(
            data=request.data, driver=request.user.driver_profile)
        if not serializer.is_valid():
            return error_with_text(serializer.errors)

        phone_change_request: PhoneNumberChangeRequest = serializer.validated_data[
            'confirmation_code']

        driver: DriverProfile = phone_change_request.driver
        driver.phone_number = phone_change_request.new_phone_number
        driver.save()
        phone_change_request.delete()

        Token.objects.filter(user=driver.user).delete()
        token = Token.objects.create(user=driver.user)
        return success_with_text({'token': token.key})
