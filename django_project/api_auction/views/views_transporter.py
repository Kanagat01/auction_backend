from backend.global_functions import success_with_text, error_with_text
from rest_framework.views import APIView
from rest_framework.request import Request
from api_auction.models import *
from api_auction.serializers import *
from api_users.models import *
from api_users.permissions.transporter_permissions import IsTransporterManagerAccount


class AddDriverData(APIView):
    permission_classes = [IsTransporterManagerAccount]

    def post(self, request: Request):
        order_id = request.data.pop("order_id")
        order_serializer = TransporterGetOrderByIdSerializer(
            data={"order_id": order_id}, context={'request': request})
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
        return success_with_text(DriverProfileSerializer(driver).data)
