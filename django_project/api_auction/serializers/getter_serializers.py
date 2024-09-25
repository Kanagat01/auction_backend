from api_auction.models import *
from rest_framework import serializers


class BaseCustomerSerializer(serializers.Serializer):
    def __init__(self, customer_manager: CustomerManager, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.customer_manager = customer_manager


class CustomerGetOrderByIdSerializer(BaseCustomerSerializer):
    """
    Сериализатор для получения заказа по ID для заказчика (менеджера заказчика) (CustomerManager)
    Если заказ не
    """
    order_id = serializers.IntegerField()

    def validate_order_id(self, value):

        try:
            a: OrderModel = OrderModel.objects.get(
                id=value, customer_manager__company=self.customer_manager.company)
        except OrderModel.DoesNotExist:
            raise serializers.ValidationError(
                "OrderModel with this ID does not exist.")

        return a


class CustomerGetOrderCoupleSerializer(BaseCustomerSerializer):
    order_stage_id = serializers.IntegerField()

    def validate_order_stage_id(self, value):
        try:
            a: OrderStageCouple = OrderStageCouple.objects.get(id=value)
        except OrderStageCouple.DoesNotExist:
            raise serializers.ValidationError(
                "OrderStageCouple with this ID does not exist.")

        return a


class DriverGetOrderCoupleSerializer(serializers.Serializer):
    order_stage_id = serializers.IntegerField()

    def __init__(self, driver: DriverProfile, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.driver = driver

    def validate_order_stage_id(self, value):
        try:
            order_stage_couple: OrderStageCouple = OrderStageCouple.objects.get(
                id=value)
            if order_stage_couple.order.driver != self.driver:
                raise serializers.ValidationError(
                    "order_stage_couple does not belong to you")
        except OrderStageCouple.DoesNotExist:
            raise serializers.ValidationError(
                "order_stage_couple does not exist")
        return order_stage_couple


class GetDocumentByIdSerializer(BaseCustomerSerializer):
    document_id = serializers.IntegerField()

    def validate_document_id(self, value):
        try:
            a: OrderDocument = OrderDocument.objects.get(id=value)
        except OrderDocument.DoesNotExist:
            raise serializers.ValidationError(
                "OrderDocument with this ID does not exist.")
        return a


class DriverGetDocumentByIdSerializer(serializers.Serializer):
    document_id = serializers.IntegerField()

    def __init__(self, driver: DriverProfile, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.driver = driver

    def validate_document_id(self, value):
        try:
            doc: OrderDocument = OrderDocument.objects.get(id=value)
            if doc.user != self.driver.user:
                raise serializers.ValidationError(
                    "document does not belong to you")
        except OrderDocument.DoesNotExist:
            raise serializers.ValidationError(
                "document does not exist")
        return doc


class TransporterGetOrderByIdSerializer(serializers.Serializer):
    """
    Сериализатор для получения заказа по ID для перевозчика (менеджера перевозчика) (TransporterManager)
    Если менеджер перевозчика не имеет доступа к заказу, то будет возвращена ошибка
    """
    order_id = serializers.IntegerField()

    def __init__(self,transporter_manager: TransporterManager, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.transporter_manager: TransporterManager = transporter_manager

    def validate_order_id(self, value):
        try:
            a: OrderModel = OrderModel.objects.get(id=value)

            # проверяем, что transport_manager может видеть этот заказ
            if not a.is_transporter_manager_allowed(self.transporter_manager):
                raise serializers.ValidationError(
                    "You are not allowed to see OrderModel with this ID.")

        except OrderModel.DoesNotExist:
            raise serializers.ValidationError(
                "OrderModel with this ID does not exist")

        return a


class DriverGetOrderByIdSerializer(serializers.Serializer):
    """
    Сериализатор для получения заказа по ID для водителя (DriverProfile)
    Если водитель не имеет доступа к заказу, то будет возвращена ошибка
    """
    order_id = serializers.IntegerField()

    def __init__(self, driver: DriverProfile, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.driver = driver

    def validate_order_id(self, value):
        try:
            order: OrderModel = OrderModel.objects.get(id=value)
            if order.driver != self.driver:
                raise serializers.ValidationError(
                    "order_does_not_belong_to_you")
        except OrderModel.DoesNotExist:
            raise serializers.ValidationError(
                "order_does_not_exist")
        return order


class GetOrderOfferByIdSerializer(serializers.Serializer):
    order_offer_id = serializers.IntegerField()

    def validate_order_offer_id(self, value):
        try:
            a = OrderOffer.objects.get(id=value)
            # if we pass request in context, we will check if the order_offer belongs to the company
            if self.context.get('request', False):
                customer_manager: CustomerManager = self.context['request'].user.customer_manager
                if a.order.customer_manager.company != customer_manager.company:
                    raise serializers.ValidationError(
                        "OrderOffer with this ID does not belong to your company.")

        except OrderOffer.DoesNotExist:
            raise serializers.ValidationError(
                "OrderOffer with this ID does not exist.")

        return a
