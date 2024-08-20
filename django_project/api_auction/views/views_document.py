from api_users.models import UserTypes
from api_users.permissions import IsTransporterManagerAccount, IsCustomerManagerAccount, IsDriverAccount
from backend.global_functions import success_with_text, error_with_text
from rest_framework.views import APIView
from rest_framework.request import Request
from api_auction.serializers import *


class AddDocumentView(APIView):
    permission_classes = [IsCustomerManagerAccount |
                          IsTransporterManagerAccount | IsDriverAccount]

    def post(self, request: Request):
        if request.user.user_type == UserTypes.CUSTOMER_MANAGER:
            serializer = CustomerGetOrderByIdSerializer(
                data=request.data, context={'request': request})
            serializer.is_valid(raise_exception=True)
            order = serializer.validated_data['order_id']
        elif request.user.user_type == UserTypes.CUSTOMER_MANAGER:
            serializer = TransporterGetOrderByIdSerializer(
                data=request.data, context={'request': request})
            serializer.is_valid(raise_exception=True)
            order: OrderModel = serializer.validated_data['order_id']
            if order.transporter_manager.company != request.user.transporter_manager.company:
                return error_with_text('OrderModel with this ID does not belong to your company.')
        else:
            # TODO: add document for driver
            pass

        request.data['order'] = order.pk
        document_serializer = OrderDocumentSerializer(data=request.data)
        if not document_serializer.is_valid():
            return error_with_text(document_serializer.errors)

        document_serializer.save(user=request.user, order=order)
        return success_with_text(OrderSerializer(order).data)


class DeleteDocumentView(APIView):
    permission_classes = [IsCustomerManagerAccount | IsDriverAccount]

    def post(self, request: Request):
        if request.user.user_type == UserTypes.CUSTOMER_MANAGER:
            serializer = GetDocumentByIdSerializer(
                data=request.data, context={'request': request})
        else:
            # TODO:delete document for driver
            pass
        serializer.is_valid(raise_exception=True)
        document = serializer.validated_data['document_id']
        document.delete()
        return success_with_text('ok')
