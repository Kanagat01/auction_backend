from rest_framework.views import APIView
from rest_framework.request import Request
from api_notification.models import Notification, NotificationType
from api_auction.models import OrderStatus, OrderStageCouple, OrderModel
from api_auction.serializers import OrderSerilizerForDriver, DriverGetOrderCoupleSerializer
from api_users.models import DriverProfile
from api_users.permissions.driver_permissions import IsDriverAccount
from backend.global_functions import success_with_text, error_with_text


class GetOrders(APIView):
    permission_classes = [IsDriverAccount]

    def get(self, request: Request):
        driver: DriverProfile = request.user.driver_profile
        orders = driver.orders.filter(status=OrderStatus.being_executed)
        if not orders.exists():
            return error_with_text("you don't have being executed orders")
        return success_with_text(OrderSerilizerForDriver(orders, driver=driver, many=True).data)


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

        order: OrderModel = order_stage_couple.order
        if order.stages.count() == order.stages.filter(load_stage__completed=True, unload_stage__completed=True).count():
            for user in [order.transporter_manager.user, order.customer_manager.user]:
                Notification.objects.create(
                    user=user,
                    title="Водитель завершил заказ",
                    description=f'Все поставки по транспортировке №{order.transportation_number} были завершены.',
                    type=NotificationType.INFO
                )
        return success_with_text(OrderSerilizerForDriver(order_stage_couple.order, driver=driver).data)
