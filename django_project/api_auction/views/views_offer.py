from backend.global_functions import success_with_text, error_with_text
from rest_framework.views import APIView
from rest_framework.request import Request
from api_auction.models import *
from api_auction.serializers import *
from api_users.permissions.transporter_permissions import IsTransporterManagerAccount
from api_users.permissions.customer_permissions import IsCustomerManagerAccount
from api_notification.models import Notification


class GetOffers(APIView):
    permission_classes = [IsTransporterManagerAccount]

    def get(self, request: Request):
        offers = OrderOffer.objects.filter(
            transporter_manager=request.user.transporter_manager)
        return success_with_text(OrderOfferSerializer(offers, many=True).data)


class AddOrderOfferView(APIView):
    permission_classes = [IsTransporterManagerAccount]

    def post(self, request: Request):
        serializer = AddOfferToOrderSerializer(
            data=request.data, context={'request': request})
        if not serializer.is_valid():
            return error_with_text(serializer.errors)

        order: OrderModel = serializer.validated_data['order_id']
        price = serializer.validated_data['price']
        if order.status == OrderStatus.in_auction:
            lowest_price = OrderOffer.get_lowest_price_for(order)
            if price > lowest_price - order.price_step:
                return error_with_text(f'not_valid_price. Price must be less than {lowest_price - order.price_step}')

        OrderOffer.objects.create(
            order=order, transporter_manager=request.user.transporter_manager, price=price)
        return success_with_text('ok')


class AcceptOffer(APIView):
    permission_classes = [IsCustomerManagerAccount]

    def post(self, request: Request):
        serializer = GetOrderOfferByIdSerializer(
            data=request.data, context={'request': request})
        if not serializer.is_valid():
            return error_with_text(serializer.errors)

        offer: OrderOffer = serializer.validated_data['order_offer_id']
        offer.make_accepted()
        Notification.objects.create(
            user=offer.transporter_manager.user,
            title=f"Ваше предложение принято",
            description=f'Ваше предложение на транспортировку №{offer.order.transportation_number} было принято. Статус заказа изменен на "Выполняется"'
        )
        return success_with_text(OrderSerializer(offer.order).data)


class RejectOffer(APIView):
    permission_classes = [IsCustomerManagerAccount]

    def post(self, request: Request):
        serializer = GetOrderOfferByIdSerializer(
            data=request.data, context={'request': request})
        if not serializer.is_valid():
            return error_with_text(serializer.errors)

        offer: OrderOffer = serializer.validated_data['order_offer_id']
        offer.make_rejected()

        return success_with_text(OrderSerializer(offer.order).data)


class RejectOfferTransporter(APIView):
    """
    Когда назначили заказ чеерез "напрямую", тогда перевозчик может отменить
    Вот это для этого и надо))
    """
    permission_classes = [IsTransporterManagerAccount]

    def post(self, request: Request):
        serializer = GetOrderOfferByIdSerializer(data=request.data)
        if not serializer.is_valid():
            return error_with_text(serializer.errors)

        offer: OrderOffer = serializer.validated_data['order_offer_id']
        if offer.transporter_manager != request.user.transporter_manager:
            return error_with_text('You are not the owner of this offer')
        offer.make_rejected()
        Notification.objects.create(
            user=offer.order.customer_manager.user,
            title=f"Заказ отклонена",
            description=f"Транспортировка №{offer.order.transportation_number} отклонена Перевозчиком {offer.transporter_manager.company.company_name}"
        )

        return success_with_text(OrderSerializer(offer.order).data)


class AcceptOfferTransporter(APIView):
    permission_classes = [IsTransporterManagerAccount]

    def post(self, request: Request):
        serializer = GetOrderOfferByIdSerializer(data=request.data)
        if not serializer.is_valid():
            return error_with_text(serializer.errors)

        offer: OrderOffer = serializer.validated_data['order_offer_id']
        if offer.transporter_manager != request.user.transporter_manager:
            return error_with_text('You are not the owner of this offer')
        offer.make_accepted()
        Notification.objects.create(
            user=offer.order.customer_manager.user,
            title=f"Заказ перешла в работу",
            description=f"Транспортировка №{offer.order.transportation_number} принята Перевозчиком {offer.transporter_manager.company.company_name}"
        )
        return success_with_text(OrderSerializer(offer.order).data)
