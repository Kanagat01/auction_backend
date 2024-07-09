from api_auction.models import *
from rest_framework import serializers

from api_users.models import TransporterCompany, DriverProfile
from .getter_serializers import CustomerGetOrderByIdSerializer, TransporterGetOrderByIdSerializer, \
    BaseCustomerSerializer


class PublishOrderToSerializer(CustomerGetOrderByIdSerializer):
    publish_to = serializers.CharField()

    def validate_publish_to(self, value):
        if value not in OrderStatus.publish_to_choices():
            raise serializers.ValidationError(
                f'Invalid publish_to value. Values are: {OrderStatus.publish_to_choices()}')
        return value


class PublishToDirectSerializer(BaseCustomerSerializer):
    transporter_company_id = serializers.IntegerField()
    price = serializers.IntegerField(min_value=0)

    def validate_transporter_company_id(self, value):
        try:
            transporter_company: TransporterCompany = TransporterCompany.objects.get(
                id=value)
            if not self.customer_manager.company.is_transporter_company_allowed(transporter_company):
                raise serializers.ValidationError(
                    'TransporterCompany is not in allowed companies')
            if transporter_company.get_manager() is None:
                raise serializers.ValidationError(
                    'TransporterCompany has no manager')
        except TransporterCompany.DoesNotExist:
            raise serializers.ValidationError(
                'TransporterCompany with this ID does not exist')
        return transporter_company


class AddOfferToOrderSerializer(TransporterGetOrderByIdSerializer):
    price = serializers.IntegerField()

    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError('Price must be greater than 0')
        return value

    def validate_order_id(self, value):
        order = super().validate_order_id(value)
        if order.status not in [OrderStatus.in_auction, OrderStatus.in_bidding]:
            raise serializers.ValidationError(
                'Order is not in auction or bidding')
        if order.offers.filter(transporter_manager=self.transporter_manager).exists():
            raise serializers.ValidationError('You have already offered')
        return order


class AddDriverDataSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField()

    class Meta:
        model = DriverProfile
        fields = ['machine_data', 'machine_number',
                  'passport_number', 'phone_number', 'full_name']

    def validate_full_name(self, value):
        if value == "":
            raise serializers.ValidationError("full_name required")
        elif len(value) > 300:
            raise serializers.ValidationError(
                "full_name should be less than 300 symbols")
        return value
