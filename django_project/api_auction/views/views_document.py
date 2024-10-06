from api_users.models import UserTypes
from api_users.permissions import IsActiveUser, IsCustomerCompanyAccount, IsCustomerManagerAccount, IsDriverAccount
from backend.global_functions import success_with_text, error_with_text
from rest_framework.views import APIView
from rest_framework.request import Request
from api_auction.serializers import *


class PrintOrder(APIView):
    permission_classes = [IsActiveUser]

    def get(self, request):
        pass


class AddDocumentView(APIView):
    permission_classes = [IsActiveUser]

    def post(self, request: Request):
        user = request.user
        user_type_check1 = user.user_type in [
            UserTypes.CUSTOMER_MANAGER, UserTypes.CUSTOMER_COMPANY]
        user_type_check2 = user.user_type in [
            UserTypes.TRANSPORTER_MANAGER, UserTypes.TRANSPORTER_COMPANY]

        if user_type_check1:
            customer_manager = user.customer_manager if hasattr(
                user, "customer_manager") else user.customer_company.managers.first()
            serializer = CustomerGetOrderByIdSerializer(
                data=request.data, customer_manager=customer_manager)
            if not serializer.is_valid():
                return error_with_text(serializer.errors)

            order = serializer.validated_data['order_id']

        elif user_type_check2:
            transporter_manager = user.transporter_manager if hasattr(
                user, "transporter_manager") else user.transporter_company.get_manager()
            serializer = TransporterGetOrderByIdSerializer(
                data=request.data, transporter_manager=transporter_manager)
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

        if user_type_check1:
            return success_with_text(OrderSerializer(order).data)
        elif user_type_check2:
            return success_with_text(OrderSerializerForTransporter(order, transporter_manager=user.transporter_manager).data)
        else:
            return success_with_text(OrderSerilizerForDriver(order, driver=user.driver_profile).data)


class DeleteDocumentView(APIView):
    permission_classes = [IsActiveUser,
                          IsCustomerCompanyAccount | IsCustomerManagerAccount | IsDriverAccount]

    def post(self, request: Request):
        if request.user.user_type == UserTypes.DRIVER:
            serializer = DriverGetDocumentByIdSerializer(
                data=request.data, driver=request.user.driver_profile)
        else:
            user: UserModel = request.user
            customer_manager = user.customer_manager if user.user_type == UserTypes.CUSTOMER_MANAGER else user.customer_company.managers.first()
            serializer = GetDocumentByIdSerializer(
                data=request.data, customer_manager=customer_manager)

        if not serializer.is_valid():
            return error_with_text(serializer.errors)

        document = serializer.validated_data['document_id']
        document.delete()
        return success_with_text('ok')
