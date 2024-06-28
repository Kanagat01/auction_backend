from backend.global_functions import success_with_text, error_with_text
from rest_framework.views import APIView
from rest_framework.request import Request
from api_auction.models import *
from api_auction.serializers import *
from api_users.models import *
from api_users.permissions.transporter_permissions import IsTransporterManagerAccount
from rest_framework.pagination import PageNumberPagination


class PaginationClass(PageNumberPagination):
    page_size = 20


def get_orders_view_decorator(cls):
    class GetOrdersView(APIView):
        permission_classes = [IsTransporterManagerAccount]

        def get(self, request: Request):
            a = cls()
            orders = a.get_orders(request)
            for_bidding = a.for_bidding if hasattr(a, 'for_bidding') else False
            page = PaginationClass().paginate_queryset(orders, request)
            return success_with_text(OrderSerializerForTransporter(page, many=True, for_bidding=for_bidding,
                                                                   transporter_manager=request.user.transporter_manager).data)

    return GetOrdersView


@get_orders_view_decorator
class GetCancelledOrdersView:
    def get_orders(self, request: Request):
        company: TransporterCompany = request.user.transporter_manager.company
        allowed_companies = company.allowed_customer_companies.all()
        return OrderModel.objects.filter(customer_manager__company__in=allowed_companies,
                                         status=OrderStatus.cancelled)


@get_orders_view_decorator
class GetOrdersInAuctionView:
    def get_orders(self, request: Request):
        company: TransporterCompany = request.user.transporter_manager.company
        allowed_companies = company.allowed_customer_companies.all()
        return OrderModel.objects.filter(customer_manager__company__in=allowed_companies,
                                         status=OrderStatus.in_auction)


@get_orders_view_decorator
class GetOrdersInBiddingView:
    for_bidding = True

    def get_orders(self, request: Request):
        company: TransporterCompany = request.user.transporter_manager.company
        allowed_companies = company.allowed_customer_companies.all()
        return OrderModel.objects.filter(customer_manager__company__in=allowed_companies,
                                         status=OrderStatus.in_bidding)


@get_orders_view_decorator
class GetOrdersInDirectView:
    def get_orders(self, request: Request):
        company: TransporterCompany = request.user.transporter_manager.company
        allowed_companies = company.allowed_customer_companies.all()
        return OrderModel.objects.filter(customer_manager__company__in=allowed_companies,
                                         status=OrderStatus.in_direct)


@get_orders_view_decorator
class GetBeingExecutedOrdersViews:

    def get_orders(self, request: Request):
        company: TransporterCompany = request.user.transporter_manager.company
        allowed_companies = company.allowed_customer_companies.all()
        return OrderModel.objects.filter(customer_manager__company__in=allowed_companies,
                                         status=OrderStatus.being_executed)


@get_orders_view_decorator
class GetCompletedOrdersView:
    def get_orders(self, request: Request):
        company: TransporterCompany = request.user.transporter_manager.company
        allowed_companies = company.allowed_customer_companies.all()
        return OrderModel.objects.filter(customer_manager__company__in=allowed_companies,
                                         status=OrderStatus.completed)
