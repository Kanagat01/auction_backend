from backend.global_functions import success_with_text, error_with_text
from rest_framework.decorators import api_view, permission_classes
from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from api_auction.models import *
from api_auction.serializers import *
from api_users.models import *
from api_users.permissions.transporter_permissions import IsTransporterCompanyAccount, IsTransporterManagerAccount


class PaginationClass(PageNumberPagination):
    page_size = 20


@api_view(['GET'])
@permission_classes([IsTransporterCompanyAccount | IsTransporterManagerAccount])
def get_orders_view(request: Request) -> Response:
    status_lst = [OrderStatus.cancelled, OrderStatus.in_auction, OrderStatus.in_bidding,
                  OrderStatus.in_direct, OrderStatus.being_executed, OrderStatus.completed]
    status = request.query_params.get('status')
    if status not in status_lst:
        return error_with_text("invalid_order_status")

    kwargs = {"status": status}
    if request.user.user_type == UserTypes.TRANSPORTER_MANAGER:
        company: TransporterCompany = request.user.transporter_manager.company
    else:
        company: TransporterCompany = request.user.transporter_company
    kwargs["customer_manager__company__in"] = company.allowed_customer_companies.all()

    orders = OrderModel.objects.filter(**kwargs)
    for_bidding = status == OrderStatus.in_bidding
    page = PaginationClass().paginate_queryset(orders, request)
    return success_with_text(OrderSerializerForTransporter(page, many=True, for_bidding=for_bidding,
                                                           transporter_manager=request.user.transporter_manager).data)


# def get_orders_view_decorator(cls):
#     class GetOrdersView(APIView):
#         permission_classes = [IsTransporterManagerAccount]

#         def get(self, request: Request):
#             a = cls()
#             orders = a.get_orders(request)
#             for_bidding = a.for_bidding if hasattr(a, 'for_bidding') else False
#             page = PaginationClass().paginate_queryset(orders, request)
#             return success_with_text(OrderSerializerForTransporter(page, many=True, for_bidding=for_bidding,
#                                                                    transporter_manager=request.user.transporter_manager).data)

#     return GetOrdersView


# @get_orders_view_decorator
# class GetCancelledOrdersView:
#     def get_orders(self, request: Request):
#         company: TransporterCompany = request.user.transporter_manager.company
#         allowed_companies = company.allowed_customer_companies.all()
#         return OrderModel.objects.filter(customer_manager__company__in=allowed_companies,
#                                          status=OrderStatus.cancelled)
