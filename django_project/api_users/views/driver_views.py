from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.authtoken.models import Token
from api_users.permissions import IsDriverAccount
from api_users.serializers import PhoneNumberChangeRequestSerializer, ConfirmPhoneNumberSerializer
from api_users.models import PhoneNumberChangeRequest, DriverProfile
from backend.global_functions import success_with_text, error_with_text


class RequestPhoneNumberChangeView(APIView):
    permission_classes = [IsDriverAccount]

    def post(self, request: Request):
        serializer = PhoneNumberChangeRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return error_with_text(serializer.errors)

        try:
            phone_change_request = PhoneNumberChangeRequest.objects.get(
                driver=request.user.driver_profile)
            phone_change_request.new_phone_number = serializer.validated_data['new_phone_number']
            phone_change_request.save()
        except PhoneNumberChangeRequest.DoesNotExist:
            phone_change_request = PhoneNumberChangeRequest.objects.create(
                driver=request.user.driver_profile, new_phone_number=serializer.validated_data['new_phone_number'])

        phone_change_request.generate_code()
        print(phone_change_request.confirmation_code)
        # TODO: send_sms
        return success_with_text('ok')


class ConfirmPhoneNumberChangeView(APIView):
    permission_classes = [IsDriverAccount]

    def post(self, request: Request):
        serializer = ConfirmPhoneNumberSerializer(
            data=request.data, context={"request": request})
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
