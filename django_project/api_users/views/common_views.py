from api_users.permissions import IsCustomerCompanyAccount, IsTransporterCompanyAccount
from backend.global_functions import success_with_text, error_with_text
from rest_framework.views import APIView
from rest_framework.request import Request
from api_users.models import *
from api_users.serializers import *


class GetUser(APIView):
    """
    Get user info
    """

    def get(self, request: Request):
        instance = request.user
        if instance.user_type == UserTypes.CUSTOMER_COMPANY:
            return success_with_text(CustomerCompanySerializer(instance.customer_company).data)
        elif instance.user_type == UserTypes.CUSTOMER_MANAGER:
            return success_with_text(CustomerManagerSerializer(instance.customer_manager).data)
        elif instance.user_type == UserTypes.TRANSPORTER_COMPANY:
            return success_with_text(TransporterCompanySerializer(instance.transporter_company).data)
        elif instance.user_type == UserTypes.TRANSPORTER_MANAGER:
            return success_with_text(TransporterManagerSerializer(instance.transporter_manager).data)
        elif instance.user_type == UserTypes.DRIVER:
            return success_with_text(DriverProfileSerializer(instance.driver_profile).data)
        elif instance.user_type == UserTypes.ORDER_VIEWER:
            return success_with_text(OrderViewerSerializer(instance.order_viewer).data)
        return error_with_text('user_not_found')


class RegisterManagerForCompany(APIView):
    permission_classes = [IsCustomerCompanyAccount | IsTransporterCompanyAccount]

    def post(self, request: Request):
        serializer = RegisterManagerSerializer(data=request.data)
        if not serializer.is_valid():
            return error_with_text(serializer.errors)

        email = serializer.validated_data['email']
        password = serializer.validated_data['password']
        full_name = serializer.validated_data['full_name']
        user_type = UserTypes.CUSTOMER_MANAGER if request.user.user_type == UserTypes.CUSTOMER_COMPANY else UserTypes.TRANSPORTER_MANAGER

        user = UserModel.objects.create_user(
            email=email,
            username=email,
            user_type=user_type,
            full_name=full_name
        )
        print('Retgistering manager with paswd:', password)
        if user.user_type == UserTypes.CUSTOMER_MANAGER:
            ins = CustomerManager.objects.create(user=user, company=request.user.customer_company)
            user.set_password(password)
            user.save()
            return success_with_text(CustomerManagerSerializer(ins, from_company=True).data)
        else:
            ins = TransporterManager.objects.create(user=user, company=request.user.transporter_company)
            user.set_password(password)
            user.save()
            return success_with_text(TransporterManagerSerializer(ins, from_company=True).data)
