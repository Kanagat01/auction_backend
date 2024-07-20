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
        driver_serializer = AddDriverDataSerializer(data=request.data)
        if not driver_serializer.is_valid():
            return error_with_text(driver_serializer.errors)

        full_name = driver_serializer.validated_data.pop('full_name')
        phone_number = driver_serializer.validated_data['phone_number']
        try:
            driver = DriverProfile.objects.get(phone_number=phone_number)
            driver.user_or_fullname.full_name = full_name
            driver.user_or_fullname.save()
            for key, value in driver_serializer.validated_data.items():
                setattr(driver, key, value)
            driver.save()
        except DriverProfile.DoesNotExist:
            full_name_instance = FullNameModel.objects.create(
                full_name=full_name)
            driver = DriverProfile.objects.create(
                **driver_serializer.validated_data, content_type=ContentType.objects.get_for_model(full_name_instance), object_id=full_name_instance.id
            )
        order.driver = driver
        order.save()
        return success_with_text(DriverProfileSerializer(driver).data)
