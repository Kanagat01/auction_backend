from api_auction.models import *
from rest_framework import serializers
from rest_framework.request import Request


class BaseCustomerSerializer(serializers.Serializer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'request' not in self.context:
            raise serializers.ValidationError("Request is required in context. [Contact to developer]")
        if not hasattr(self.context['request'].user, 'customer_manager'):
            raise serializers.ValidationError("Request user must be a CustomerManager. [Contact to developer]")
        self.customer_manager: CustomerManager = self.context['request'].user.customer_manager


class CustomerGetOrderByIdSerializer(BaseCustomerSerializer):
    """
    Сериализатор для получения заказа по ID для заказчика (менеджера заказчика) (CustomerManager)
    Если заказ не
    """
    order_id = serializers.IntegerField()

    def validate_order_id(self, value):

        try:
            a: OrderModel = OrderModel.objects.get(id=value)

            # проверяем, что заказ принадлежит менеджеру заказчика
            if a.customer_manager != self.customer_manager:
                raise serializers.ValidationError("OrderModel with this ID does not belong to you.")

        except OrderModel.DoesNotExist:
            raise serializers.ValidationError("OrderModel with this ID does not exist.")

        return a


class CustomerGetOrderCoupleSerializer(BaseCustomerSerializer):
    order_stage_id = serializers.IntegerField()

    def validate_order_stage_id(self, value):
        try:
            a: OrderStageCouple = OrderStageCouple.objects.get(id=value)
            if a.order.customer_manager != self.customer_manager:
                raise serializers.ValidationError("OrderStageCouple with this ID does not belong to you.")

        except OrderStageCouple.DoesNotExist:
            raise serializers.ValidationError("OrderStageCouple with this ID does not exist.")

        return a


class GetDocumentByIdSerializer(BaseCustomerSerializer):
    document_id = serializers.IntegerField()

    def validate_document_id(self, value):
        try:
            a: OrderDocument = OrderDocument.objects.get(id=value)
            if a.order.customer_manager != self.customer_manager:
                raise serializers.ValidationError("OrderDocument with this ID does not belong to you.")

        except OrderDocument.DoesNotExist:
            raise serializers.ValidationError("OrderDocument with this ID does not exist.")

        return a


class TransporterGetOrderByIdSerializer(serializers.Serializer):
    """
    Сериализатор для получения заказа по ID для перевозчика (менеджера перевозчика) (TransporterManager)
    Если менеджер перевозчика не имеет доступа к заказу, то будет возвращена ошибка
    """
    order_id = serializers.IntegerField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'request' not in self.context:
            raise serializers.ValidationError("Request is required in context. [Contact to developer]")
        if not hasattr(self.context['request'].user, 'transporter_manager'):
            raise serializers.ValidationError("Request user must be a TransporterManager. [Contact to developer]")
        self.transporter_manager: TransporterManager = self.context['request'].user.transporter_manager

    def validate_order_id(self, value):
        try:
            a: OrderModel = OrderModel.objects.get(id=value)

            # проверяем, что transport_manager может видеть этот заказ
            if not a.is_transporter_manager_allowed(self.transporter_manager):
                raise serializers.ValidationError("You are not allowed to see OrderModel with this ID.")

        except OrderModel.DoesNotExist:
            raise serializers.ValidationError("OrderModel with this ID does not exist")

        return a


class GetOrderOfferByIdSerializer(serializers.Serializer):
    order_offer_id = serializers.IntegerField()

    def validate_order_offer_id(self, value):
        try:
            a = OrderOffer.objects.get(id=value)
            # if we pass request in context, we will check if the order_offer belongs to the customer_manager
            if self.context.get('request', False):
                customer_manager: CustomerManager = self.context['request'].user.customer_manager
                if a.order.customer_manager != customer_manager:
                    raise serializers.ValidationError("OrderOffer with this ID does not belong to your order.")

        except OrderOffer.DoesNotExist:
            raise serializers.ValidationError("OrderOffer with this ID does not exist.")

        return a
