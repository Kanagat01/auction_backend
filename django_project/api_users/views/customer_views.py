from backend.global_functions import success_with_text, error_with_text
from rest_framework.views import APIView
from rest_framework.request import Request
from api_users.models import *
from api_users.serializers.model_serializers import TransporterCompanySerializer
from api_users.serializers.customer_serializers import *
from api_users.permissions.customer_permissions import IsCustomerCompanyAccount


class GetTransporterCompanies(APIView):
    permission_classes = [IsCustomerCompanyAccount]

    def get(self, request: Request):
        customer = request.user.customer_company
        companies = TransporterCompany.objects.exclude(
            id__in=customer.allowed_transporter_companies.all().values_list('id', flat=True)
        )
        return success_with_text(TransporterCompanySerializer(companies, from_manager=True, many=True).data)


class AddTransporterToAllowedCompanies(APIView):
    permission_classes = [IsCustomerCompanyAccount]

    def post(self, request: Request):
        serializer = GetTransporterCompanyById(data=request.data)

        if not serializer.is_valid():
            return error_with_text(serializer.errors)

        customer_company: CustomerCompany = request.user.customer_company
        transporter_company: TransporterCompany = serializer.validated_data[
            'transporter_company_id']

        customer_company.allowed_transporter_companies.add(transporter_company)

        return success_with_text(TransporterCompanySerializer(transporter_company, from_manager=True).data)


class DeleteTransporterFromAllowedCompanies(APIView):
    permission_classes = [IsCustomerCompanyAccount]

    def post(self, request: Request):
        serializer = GetTransporterCompanyById(data=request.data)

        if not serializer.is_valid():
            return error_with_text(serializer.errors)

        customer_company: CustomerCompany = request.user.customer_company
        transporter_company: TransporterCompany = serializer.validated_data[
            'transporter_company_id']

        customer_company.allowed_transporter_companies.remove(
            transporter_company)

        return success_with_text('ok')
