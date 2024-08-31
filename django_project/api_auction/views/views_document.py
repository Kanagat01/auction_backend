from api_users.models import UserTypes
from api_users.permissions import IsActiveUser, IsTransporterManagerAccount, IsCustomerManagerAccount, IsDriverAccount
from backend.global_functions import success_with_text, error_with_text
from rest_framework.views import APIView
from rest_framework.request import Request
from api_auction.serializers import *


class AddDocumentView(APIView):
    permission_classes = [IsActiveUser, IsCustomerManagerAccount |
                          IsTransporterManagerAccount | IsDriverAccount]

    def post(self, request: Request):
        user = request.user
        if user.user_type == UserTypes.CUSTOMER_MANAGER:
            serializer = CustomerGetOrderByIdSerializer(
                data=request.data, context={'request': request})
            if not serializer.is_valid():
                return error_with_text(serializer.errors)

            order = serializer.validated_data['order_id']

        elif user.user_type == UserTypes.TRANSPORTER_MANAGER:
            serializer = TransporterGetOrderByIdSerializer(
                data=request.data, context={'request': request})
            if not serializer.is_valid():
                return error_with_text(serializer.errors)

            order: OrderModel = serializer.validated_data['order_id']
            if order.transporter_manager and order.transporter_manager.company != user.transporter_manager.company:
                return error_with_text('OrderModel with this ID does not belong to your company')

        else:
            serializer = DriverGetOrderByIdSerializer(
                data=request.data, driver=user.driver_profile)
            if not serializer.is_valid():
                return error_with_text(serializer.errors)
            order: OrderModel = serializer.validated_data['order_id']

        request.data['order'] = order.pk
        document_serializer = OrderDocumentSerializer(data=request.data)
        if not document_serializer.is_valid():
            return error_with_text(document_serializer.errors)

        document_serializer.save(user=user, order=order)

        if user.user_type == UserTypes.CUSTOMER_MANAGER:
            return success_with_text(OrderSerializer(order).data)
        elif user.user_type == UserTypes.TRANSPORTER_MANAGER:
            return success_with_text(OrderSerializerForTransporter(order, transporter_manager=user.transporter_manager).data)
        else:
            return success_with_text(OrderSerilizerForDriver(order, driver=user.driver_profile).data)


class DeleteDocumentView(APIView):
    permission_classes = [IsActiveUser,
                          IsCustomerManagerAccount | IsDriverAccount]

    def post(self, request: Request):
        if request.user.user_type == UserTypes.CUSTOMER_MANAGER:
            serializer = GetDocumentByIdSerializer(
                data=request.data, context={'request': request})
        else:
            serializer = DriverGetDocumentByIdSerializer(
                data=request.data, driver=request.user.driver_profile)

        if not serializer.is_valid():
            return error_with_text(serializer.errors)

        document = serializer.validated_data['document_id']
        document.delete()
        return success_with_text('ok')
