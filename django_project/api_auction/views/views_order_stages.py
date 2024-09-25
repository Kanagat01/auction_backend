from backend.global_functions import success_with_text, error_with_text
from rest_framework.views import APIView
from rest_framework.request import Request
from api_auction.models import *
from api_auction.serializers import *
from api_users.permissions import IsActiveUser, IsCustomerManagerAccount


class AddStageToOrderView(APIView):
    permission_classes = [IsActiveUser, IsCustomerManagerAccount]

    def post(self, request: Request):
        customer_manager: CustomerManager = request.user.customer_manager
        serializer = CustomerGetOrderByIdSerializer(
            data=request.data, customer_manager=customer_manager)
        if not serializer.is_valid():
            return error_with_text(serializer.errors)

        stage_serializer = OrderStageCoupleSerializer(data=request.data)
        if not stage_serializer.is_valid():
            return error_with_text(stage_serializer.errors)

        stage_number = stage_serializer.validated_data['order_stage_number']
        if OrderStageCouple.check_stage_number(stage_number, customer_manager.company):
            return error_with_text('order_stage_number_must_be_unique')

        order = serializer.validated_data['order_id']
        stage_serializer.save(order=order)

        return success_with_text(OrderSerializer(order).data)


class EditStageView(APIView):
    permission_classes = [IsActiveUser, IsCustomerManagerAccount]

    def post(self, request: Request):
        serializer = CustomerGetOrderCoupleSerializer(
            data=request.data, customer_manager=request.user.customer_manager)
        if not serializer.is_valid():
            return error_with_text(serializer.errors)

        stage_couple = serializer.validated_data['order_stage_id']
        order = stage_couple.order

        if order.status != OrderStatus.unpublished:
            return error_with_text("You can edit stages only in unpublished orders.")

        a = OrderStageCoupleSerializer(
            stage_couple, data=request.data, partial=True)
        a.is_valid(raise_exception=True)

        if OrderStageCouple.check_stage_number(a.validated_data['order_stage_number'], order.customer_manager.company,
                                               stage_couple.pk):
            return error_with_text('order_stage_number_must_be_unique')

        a.save()

        return success_with_text(OrderSerializer(order).data)


class DeleteStageView(APIView):
    permission_classes = [IsActiveUser, IsCustomerManagerAccount]

    def post(self, request: Request):
        serializer = CustomerGetOrderCoupleSerializer(
            data=request.data, customer_manager=request.user.customer_manager)
        if not serializer.is_valid():
            return error_with_text(serializer.errors)

        stage_couple = serializer.validated_data['order_stage_id']
        order = stage_couple.order

        if order.status != OrderStatus.unpublished:
            return error_with_text("You can delete stages only in unpublished orders.")

        stage_couple.delete()

        return success_with_text(OrderSerializer(order).data)
