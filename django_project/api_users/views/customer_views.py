from api_users.permissions.customer_permissions import IsCustomerCompanyAccount
from backend.global_functions import success_with_text, error_with_text
from rest_framework.views import APIView
from rest_framework.request import Request
from api_users.models import *
from api_users.serializers.customer_serializers import *


class AddTransporterToAllowedCompanies(APIView):
    permission_classes = [IsCustomerCompanyAccount]

    def post(self, request: Request):
        serializer = GetTransporterCompanyById(data=request.data)

        if not serializer.is_valid():
            return error_with_text(serializer.errors)

        customer_company: CustomerCompany = request.user.customer_company
        transporter_company: TransporterCompany = serializer.validated_data['transporter_company_id']

        customer_company.allowed_transporter_companies.add(transporter_company)

        return success_with_text('ok')


class DeleteTransporterFromAllowedCompanies(APIView):
    permission_classes = [IsCustomerCompanyAccount]

    def post(self, request: Request):
        serializer = GetTransporterCompanyById(data=request.data)

        if not serializer.is_valid():
            return error_with_text(serializer.errors)

        customer_company: CustomerCompany = request.user.customer_company
        transporter_company: TransporterCompany = serializer.validated_data['transporter_company_id']

        customer_company.allowed_transporter_companies.remove(transporter_company)

        return success_with_text('ok')
