from smsaero import SmsAero, SmsAeroException
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from rest_framework.views import APIView
from rest_framework.request import Request
from api_auction.models import *
from api_auction.serializers import *
from api_users.models import *
from api_users.permissions import IsActiveUser, IsTransporterManagerAccount
from backend.global_functions import success_with_text, error_with_text


class AddDriverData(APIView):
    permission_classes = [IsActiveUser, IsTransporterManagerAccount]

    def post(self, request: Request):
        order_serializer = TransporterGetOrderByIdSerializer(
            data=request.data, transporter_manager=request.user.transporter_manager)
        if not order_serializer.is_valid():
            return error_with_text(order_serializer.errors)

        order: OrderModel = order_serializer.validated_data['order_id']
        if order.status != OrderStatus.being_executed:
            return error_with_text("Status should be being_executed")

        phone_number = request.data.get('phone_number')
        try:
            driver = DriverProfile.objects.get(phone_number=phone_number)
            driver_serializer = AddDriverDataSerializer(
                instance=driver, data=request.data)
        except DriverProfile.DoesNotExist:
            driver_serializer = AddDriverDataSerializer(data=request.data)

        if not driver_serializer.is_valid():
            return error_with_text(driver_serializer.errors)

        driver = driver_serializer.save()
        order.driver = driver
        order.save()

        user_ids = order.get_user_ids()
        user_ids.remove(request.user.pk)
        for user_id in user_ids:
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(f"user_{user_id}", {
                "type": "add_or_update_order",
                "order_id": order.pk,
            })
        return success_with_text(DriverProfileSerializer(driver).data)


SMSAERO_EMAIL = 'kargonika@yandex.ru'
SMSAERO_API_KEY = 'cEbdLCjCpjy_I43YSgwT9ARLWMogXwbk'


def send_sms(phone: int, message: str) -> dict:
    """
    Sends an SMS message

    Parameters:
    phone (int): The phone number to which the SMS message will be sent.
    message (str): The content of the SMS message to be sent.

    Returns:
    dict: A dictionary containing the response from the SmsAero API.
    """
    api = SmsAero(SMSAERO_EMAIL, SMSAERO_API_KEY)
    return api.send_sms(phone, message)


class A(APIView):
    permission_classes = ()

    def get(self, request):
        try:
            result = send_sms(77762747213, 'Hello, World!')
            return success_with_text(result)
        except SmsAeroException as e:
            return error_with_text(f"An error occurred: {e}")
