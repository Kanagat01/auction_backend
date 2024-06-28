from pprint import pprint

from backend.global_functions import success_with_text, error_with_text
from rest_framework.views import APIView
from rest_framework.request import Request
from api_auction.models import *
from api_auction.serializers import *
from api_users.permissions.customer_permissions import IsCustomerManagerAccount


class PreCreateOrderView(APIView):
    permission_classes = [IsCustomerManagerAccount]

    def get(self, request: Request):
        # get names of all transport body types, load types, unload types
        transport_body_types = OrderTransportBodyType.objects.all()
        transport_load_types = OrderTransportLoadType.objects.all()
        transport_unload_types = OrderTransportUnloadType.objects.all()

        return success_with_text({
            'transport_body_types': OrderTransportBodyTypeSerializer(transport_body_types, many=True).data,
            'transport_load_types': OrderTransportLoadTypeSerializer(transport_load_types, many=True).data,
            'transport_unload_types': OrderTransportUnloadTypeSerializer(transport_unload_types, many=True).data,
        })


class CreateOrderView(APIView):
    permission_classes = [IsCustomerManagerAccount]

    def post(self, request: Request):
        stages_data = request.data.pop('stages', [])
        request.data['customer_manager'] = request.user.customer_manager
        serializer = OrderSerializer(data=request.data)
        if not serializer.is_valid():
            return error_with_text(serializer.errors)

        order: OrderModel = OrderModel(
            customer_manager=request.user.customer_manager,
            **serializer.validated_data
        )

        transportation_number = order.transportation_number
        company = order.customer_manager.company
        if OrderModel.check_transportation_number(transportation_number, company):
            return error_with_text('transportation_number_must_be_unique')

        if len(stages_data) < 1:
            return error_with_text('add_at_least_one_stage')

        for stage_data in stages_data:
            stage_serializer = OrderStageCoupleSerializer(data=stage_data)
            stage_serializer.is_valid(raise_exception=True)

            stage_number = stage_serializer.validated_data.get('order_stage_number', get_unix_time())
            # check if unique within company
            if OrderStageCouple.check_stage_number(stage_number, company):
                return error_with_text('order_stage_number_must_be_unique')

            order.save()
            stage_serializer.save(order=order)

        return success_with_text(OrderSerializer(order).data)


class EditOrderView(APIView):
    permission_classes = [IsCustomerManagerAccount]

    def post(self, request: Request):

        serializer = CustomerGetOrderByIdSerializer(data=request.data, context={'request': request})
        if not serializer.is_valid():
            return error_with_text(serializer.errors)

        order: OrderModel = serializer.validated_data['order_id']
        if order.status != OrderStatus.unpublished:
            return error_with_text('You can edit only unpublished orders.')

        transportation_number = order.transportation_number
        # check if transportation number unique (within company)
        if OrderModel.check_transportation_number(transportation_number, order.customer_manager.company, order.pk):
            return error_with_text('transportation_number_must_be_unique')

        order_serializer = OrderSerializer(order, data=request.data, partial=True)
        if not order_serializer.is_valid():
            return error_with_text(order_serializer.errors)

        order.updated_at = timezone.now()
        order_serializer.save()

        return success_with_text(order_serializer.data)


class CancelOrderView(APIView):
    permission_classes = [IsCustomerManagerAccount]

    def post(self, request: Request):
        serializer = CustomerGetOrderByIdSerializer(data=request.data, context={'request': request})
        if not serializer.is_valid():
            return error_with_text(serializer.errors)

        order: OrderModel = serializer.validated_data['order_id']
        order.make.cancelled()

        #  Creating a copy of the order
        # order: OrderModel = serializer.validated_data['order_id']
        # if order.transporter_manager is not None:
        #     # create a copy of the order
        #     orig_order_pk = order.pk
        #     order.pk = None
        #     order.status = OrderStatus.cancelled
        #     order.save()
        #     order = OrderModel.objects.get(pk=orig_order_pk)
        #
        # order.make.cancelled()

        return success_with_text(OrderSerializer(order).data)


class UnpublishOrderView(APIView):
    permission_classes = [IsCustomerManagerAccount]

    def post(self, request: Request):
        serializer = CustomerGetOrderByIdSerializer(data=request.data, context={'request': request})
        if not serializer.is_valid():
            return error_with_text(serializer.errors)

        order: OrderModel = serializer.validated_data['order_id']
        order.make.unpublished()

        return success_with_text(OrderSerializer(order).data)


class PublishOrderToView(APIView):
    permission_classes = [IsCustomerManagerAccount]

    def post(self, request: Request):
        serializer = PublishOrderToSerializer(data=request.data, context={'request': request})
        if not serializer.is_valid():
            return error_with_text(serializer.errors)

        publish_to = request.data['publish_to']
        order: OrderModel = serializer.validated_data['order_id']

        if publish_to == OrderStatus.in_direct:
            direct_serializer = PublishToDirectSerializer(data=request.data, context={'request': request})
            if not direct_serializer.is_valid():
                return error_with_text(serializer.errors)
            transporter_manager = direct_serializer.validated_data['transporter_company_id'].get_manager()
            price = direct_serializer.validated_data['price']
            OrderOffer.objects.create(order=order, transporter_manager=transporter_manager, price=price)

        order.make.published_to(publish_to)

        return success_with_text(OrderSerializer(order).data)


class CompleteOrderView(APIView):
    permission_classes = [IsCustomerManagerAccount]

    def post(self, request: Request):
        serializer = CustomerGetOrderByIdSerializer(data=request.data, context={'request': request})
        if not serializer.is_valid():
            return error_with_text(serializer.errors)

        order: OrderModel = serializer.validated_data['order_id']
        order.make.completed()

        return success_with_text(OrderSerializer(order).data)
