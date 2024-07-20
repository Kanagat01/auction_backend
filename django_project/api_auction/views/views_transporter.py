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

    if status == OrderStatus.being_executed:
        status_filter = Q(status=OrderStatus.being_executed) | Q(
            status=OrderStatus.completed)
    else:
        status_filter = Q(status=status)

    if request.user.user_type == UserTypes.TRANSPORTER_MANAGER:
        company: TransporterCompany = request.user.transporter_manager.company
    else:
        company: TransporterCompany = request.user.transporter_company

    orders = OrderModel.objects.filter(
        status_filter, customer_manager__company__in=company.allowed_customer_companies.all())
    for_bidding = status == OrderStatus.in_bidding
    paginator = PaginationClass()
    page = paginator.paginate_queryset(orders, request)

    if request.user.user_type == UserTypes.TRANSPORTER_MANAGER:
        result = OrderSerializerForTransporter(
            page,
            many=True,
            for_bidding=for_bidding,
            transporter_manager=request.user.transporter_manager
        ).data
    else:
        result = [
            OrderSerializerForTransporter(
                order,
                for_bidding=for_bidding,
                transporter_manager=order.transporter_manager
            ).data for order in page if order.transporter_manager is not None
        ]
    pagination_data = {
        'pages_total': paginator.page.paginator.num_pages,
        'current_page': paginator.page.number
    }
    return success_with_text({'pagination': pagination_data, 'orders': result})


class AddDriverData(APIView):
    permission_classes = [IsTransporterCompanyAccount |
                          IsTransporterManagerAccount]

    def post(self, request: Request):
        order_id = request.data.pop("order_id")
        order_serializer = TransporterGetOrderByIdSerializer(
            data={"order_id": order_id}, context={'request': request})
        if not order_serializer.is_valid():
            return error_with_text(order_serializer.errors)

        order: OrderModel = order_serializer.validated_data['order_id']
        if order.driver:
            return error_with_text("This order already have a driver")

        driver_serializer = AddDriverDataSerializer(data=request.data)
        if not driver_serializer.is_valid():
            return error_with_text(driver_serializer.errors)

        full_name = driver_serializer.validated_data.pop('full_name')
        phone_number = driver_serializer.validated_data['phone_number']

        try:
            driver = DriverProfile.objects.get(phone_number=phone_number)
            driver.user_or_fullname.full_name = full_name
            driver.user_or_fullname.save()
        except DriverProfile.DoesNotExist:
            full_name_instance = FullNameModel.objects.create(
                full_name=full_name)
            driver = DriverProfile.objects.create(
                **driver_serializer.validated_data, content_type=ContentType.objects.get_for_model(full_name_instance), object_id=full_name_instance.id
            )
        order.driver = driver
        order.save()
        return success_with_text(DriverProfileSerializer(driver).data)
