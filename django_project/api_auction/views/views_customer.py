from backend.global_functions import success_with_text, error_with_text
from rest_framework.decorators import api_view, permission_classes
from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from api_auction.models import *
from api_auction.serializers import *
from api_users.models.user import UserTypes
from api_users.permissions.customer_permissions import IsCustomerCompanyAccount, IsCustomerManagerAccount


class PaginationClass(PageNumberPagination):
    page_size = 20


@api_view(['GET'])
@permission_classes([IsCustomerCompanyAccount | IsCustomerManagerAccount])
def get_orders_view(request: Request) -> Response:
    status_lst = [OrderStatus.unpublished, OrderStatus.cancelled, OrderStatus.in_auction, OrderStatus.in_bidding,
                  OrderStatus.in_direct, OrderStatus.being_executed, OrderStatus.completed]
    status = request.query_params.get('status')
    if status not in status_lst:
        return error_with_text("invalid_order_status")

    kwargs = {"status": status}
    if request.user.user_type == UserTypes.CUSTOMER_MANAGER:
        kwargs["customer_manager"] = request.user.customer_manager
    else:
        kwargs['customer_manager__company'] = request.user.customer_company

    orders = OrderModel.objects.filter(**kwargs)
    paginator = PaginationClass()
    page = paginator.paginate_queryset(orders, request)

    pagination_data = {
        'pages_total': paginator.page.paginator.num_pages,
        'current_page': paginator.page.number
    }
    return success_with_text({'pagination': pagination_data, 'orders': OrderSerializer(page, many=True).data})


# def get_orders_view_decorator(cls):
#     class GetOrdersView(APIView):
#         permission_classes = [
#             IsCustomerCompanyAccount | IsCustomerManagerAccount]

#         def get(self, request: Request):
#             orders = cls().get_orders(request)
#             page = PaginationClass().paginate_queryset(orders, request)
#             return success_with_text(OrderSerializer(page, many=True).data)

#     return GetOrdersView


# @get_orders_view_decorator
# class GetUnpublishedOrdersView:
#     def get_orders(self, request: Request):
#         return OrderModel.objects.filter(customer_manager=request.user.customer_manager,
#                                          status=OrderStatus.unpublished)
