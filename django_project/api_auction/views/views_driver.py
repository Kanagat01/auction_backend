from backend.global_functions import success_with_text, error_with_text
from rest_framework.views import APIView
from rest_framework.request import Request
from api_auction.models import OrderStatus, OrderStageCouple
from api_auction.serializers import OrderSerilizerForDriver, DriverGetOrderCoupleSerializer
from api_users.models import DriverProfile
from api_users.permissions.driver_permissions import IsDriverAccount


class GetOrder(APIView):
    permission_classes = [IsDriverAccount]

    def get(self, request: Request):
        driver: DriverProfile = request.user.driver_profile
        orders = driver.orders.filter(status=OrderStatus.being_executed)
        if not orders.exists():
            return error_with_text("you don't have being executed orders")
        return success_with_text(OrderSerilizerForDriver(orders.first(), driver=driver).data)


class MakeOrderStageCompleted(APIView):
    permission_classes = [IsDriverAccount]

    def post(self, request):
        driver: DriverProfile = request.user.driver_profile
        serializer = DriverGetOrderCoupleSerializer(
            data=request.data, driver=driver)
        if not serializer.is_valid():
            return error_with_text(serializer.errors)

        order_stage_couple: OrderStageCouple = serializer.validated_data["order_stage_id"]
        if not order_stage_couple.load_stage.completed:
            order_stage_couple.load_stage.completed = True
            order_stage_couple.load_stage.save()
        elif not order_stage_couple.unload_stage.completed:
            order_stage_couple.unload_stage.completed = True
            order_stage_couple.unload_stage.save()
        return success_with_text(OrderSerilizerForDriver(order_stage_couple.order, driver=driver).data)
