from rest_framework import serializers
from api_users.models import TransporterCompany
from api_users.models import UserModel


class GetTransporterCompanyById(serializers.Serializer):
    transporter_company_id = serializers.IntegerField()

    def validate_transporter_company_id(self, transporter_company_id):
        try:
            transporter_company = TransporterCompany.objects.get(id=transporter_company_id)
        except TransporterCompany.DoesNotExist:
            raise serializers.ValidationError("TransporterCompany with this ID does not exist.")
        return transporter_company
