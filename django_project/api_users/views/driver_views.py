from smsaero import SmsAeroException
from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.authtoken.models import Token
from api_users.permissions import IsDriverAccount
from api_users.serializers import DriverProfileSerializer
from api_users.serializers.driver_serializers import *
from api_users.models import UserModel, UserTypes, PhoneNumberChangeRequest, DriverProfile, DriverRegisterRequest
from backend.global_functions import send_sms, success_with_text, error_with_text


class RegisterDriverRequest(APIView):
    permission_classes = ()

    def post(self, request: Request):
        serializer = RegisterDriverRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return error_with_text(serializer.errors)

        phone_number = serializer.validated_data['phone_number']
        try:
            driver_register_request = DriverRegisterRequest.objects.get(
                phone_number=phone_number)
        except DriverRegisterRequest.DoesNotExist:
            driver_register_request = DriverRegisterRequest.objects.create(
                phone_number=phone_number)

        driver_register_request.generate_code()
        print(driver_register_request.confirmation_code)

        try:
            result = send_sms(
                int(phone_number), driver_register_request.confirmation_code)
            return success_with_text(result)
        except SmsAeroException as e:
            print(e)
            return error_with_text('sms_service_error: ' + str(e))


class RegisterDriverConfirm(APIView):
    permission_classes = ()

    def post(self, request: Request):
        serializer = RegisterDriverConfirmSerializer(data=request.data)
        if not serializer.is_valid():
            return error_with_text(serializer.errors)

        driver_register_request: DriverRegisterRequest = serializer.validated_data[
            'driver_register_request']

        phone_number = driver_register_request.phone_number
        try:
            driver = DriverProfile.objects.get(phone_number=phone_number)
            user = driver.user
            Token.objects.filter(user=user).delete()
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
        token = Token.objects.create(user=user)
        return success_with_text({'token': token.key, "driver_exist": driver_exist})


class SetDriverProfileData(APIView):
    permission_classes = [IsDriverAccount]

    def post(self, request: Request):
        user: UserModel = request.user
        if hasattr(user, 'driver_profile'):
            serializer = SetDriverPasswordAndBirthDate(data=request.data)
            if not serializer.is_valid():
                print(serializer.errors)
                return error_with_text(serializer.errors)

            birth_date = serializer.validated_data["birth_date"]
            if birth_date:
                user.driver_profile.birth_date = birth_date
                user.driver_profile.save()

            user.set_password(
                serializer.validated_data["new_password"])
            user.save()
        else:
            serializer = SetDriverProfileDataSerializer(
                data={"phone_number": user.username, **request.data}
            )
            if not serializer.is_valid():
                return error_with_text(serializer.errors)

            serializer.validated_data.pop("confirm_password")
            password = serializer.validated_data.pop("new_password")
            full_name = serializer.validated_data.pop("full_name")

            DriverProfile.objects.create(
                user=user, **serializer.validated_data)

            user.full_name = full_name
            user.set_password(password)
            user.save()

        return success_with_text(DriverProfileSerializer(user.driver_profile).data)


class RequestPhoneNumberChangeView(APIView):
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
                int(phone_number), phone_change_request.confirmation_code)
            return success_with_text(result)
        except SmsAeroException as e:
            print(e)
            return error_with_text('sms_service_error: ' + str(e))


class ConfirmPhoneNumberChangeView(APIView):
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
