from backend.global_functions import success_with_text
from rest_framework.views import APIView
from rest_framework.request import Request
from api_auction.models import OrderStatus
from api_auction.serializers import OrderSerilizerForDriver
from api_users.models import DriverProfile
from api_users.permissions.driver_permissions import IsDriverAccount


class GetOrder(APIView):
    permission_classes = [IsDriverAccount]

    def get(self, request: Request):
        driver: DriverProfile = request.user.driver_profile
        orders = driver.orders.filter(status=OrderStatus.being_executed)
        if not orders.exists():
            return success_with_text("you don't have being executed orders")
        return success_with_text(OrderSerilizerForDriver(orders.first(), driver=driver).data)
