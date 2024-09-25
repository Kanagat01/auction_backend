from django.forms import model_to_dict
from django.db.models import Max
from rest_framework.views import APIView
from rest_framework.request import Request

from api_auction.models import *
from api_auction.serializers import *
from api_notification.models import Notification, NotificationType
from api_users.permissions import IsActiveUser, IsCustomerManagerAccount
from backend.global_functions import success_with_text, error_with_text


class PreCreateOrderView(APIView):
    permission_classes = [IsActiveUser, IsCustomerManagerAccount]

    def get(self, request: Request):
        # get names of all transport body types, load types, unload types
        transport_body_types = OrderTransportBodyType.objects.all()
        transport_load_types = OrderTransportLoadType.objects.all()
        transport_unload_types = OrderTransportUnloadType.objects.all()
        response = {
            'transport_body_types': OrderTransportBodyTypeSerializer(transport_body_types, many=True).data,
            'transport_load_types': OrderTransportLoadTypeSerializer(transport_load_types, many=True).data,
            'transport_unload_types': OrderTransportUnloadTypeSerializer(transport_unload_types, many=True).data,
        }
        orders = OrderModel.objects.filter(
            customer_manager__company=request.user.customer_manager.company
        )
        transportation_number = request.query_params.get(
            'transportation_number')
        if (transportation_number and transportation_number.isdigit()):
            try:
                order = OrderModel.objects.get(customer_manager__company=request.user.customer_manager.company,
                                               transportation_number=int(transportation_number))
                response["order"] = OrderSerializer(order).data
            except OrderModel.DoesNotExist:
                return error_with_text("order_not_found")
        else:
            max_transportation_number = orders.aggregate(Max('transportation_number'))[
                'transportation_number__max']
            response["max_transportation_number"] = max_transportation_number if max_transportation_number else 0

        max_order_stage_number = OrderStageCouple.objects.filter(order__in=orders).aggregate(
            Max('order_stage_number'))['order_stage_number__max']
        response["max_order_stage_number"] = max_order_stage_number if max_order_stage_number else 0
        return success_with_text(response)


class CreateOrderView(APIView):
    permission_classes = [IsActiveUser, IsCustomerManagerAccount]

    def post(self, request: Request):
        stages_data = request.data.pop('stages', [])
        request.data['customer_manager'] = request.user.customer_manager
        serializer = OrderSerializer(data=request.data)
        if not serializer.is_valid():
            return error_with_text(serializer.errors)

        order: OrderModel = OrderModel(
            customer_manager=request.user.customer_manager,
            **serializer.validated_data
        )

        transportation_number = order.transportation_number
        company = order.customer_manager.company
        if OrderModel.check_transportation_number(transportation_number, company):
            return error_with_text('transportation_number_must_be_unique')

        if len(stages_data) < 1:
            return error_with_text('add_at_least_one_stage')

        stages = []
        for stage_data in stages_data:
            stage_serializer = OrderStageCoupleSerializer(data=stage_data)
            stage_serializer.is_valid(raise_exception=True)

            stage_number = stage_serializer.validated_data.get(
                'order_stage_number', get_unix_time())
            # check if unique within company
            if OrderStageCouple.check_stage_number(stage_number, company):
                return error_with_text(f'order_stage_number_must_be_unique:{stage_number}')

            stages.append(stage_serializer)

        for stage in stages:
            order.save()
            stage.save(order=order)

        orders = OrderModel.objects.filter(
            customer_manager__company=request.user.customer_manager.company
        )
        max_transportation_number = orders.aggregate(Max('transportation_number'))[
            'transportation_number__max']
        max_order_stage_number = OrderStageCouple.objects.filter(order__in=orders).aggregate(
            Max('order_stage_number'))['order_stage_number__max']

        return success_with_text({
            "max_transportation_number": max_transportation_number if max_transportation_number else 0,
            "max_order_stage_number": max_order_stage_number if max_order_stage_number else 0
        })


def update_stages(customer_manager: CustomerManager, order: OrderModel, stages_data: list):
    add_stages = []
    stage_data_dict = {}
    for s in stages_data:
        if "id" in s:
            stage_data_dict[s["id"]] = s
        else:
            add_stages.append(s)

    delete_stages = []
    edit_stages = []
    for stage in OrderStageCouple.objects.filter(order=order):
        if stage.pk not in stage_data_dict.keys():
            delete_stages.append(model_to_dict(stage))
        else:
            edit_stages.append(stage_data_dict[stage.pk])

    for idx, stage_data in enumerate(delete_stages):
        stage_data["order_stage_id"] = stage_data.pop("id")
        serializer = CustomerGetOrderCoupleSerializer(
            data=stage_data, customer_manager=customer_manager)
        if not serializer.is_valid():
            return error_with_text(serializer.errors)

        delete_stages[idx] = serializer.validated_data['order_stage_id']

    for idx, stage_data in enumerate(edit_stages):
        stage_data["order_stage_id"] = stage_data.pop("id")
        serializer = CustomerGetOrderCoupleSerializer(
            data=stage_data, customer_manager=customer_manager)
        if not serializer.is_valid():
            return error_with_text(serializer.errors)

        order_stage_id = serializer.validated_data['order_stage_id']

        stage_couple = OrderStageCoupleSerializer(
            order_stage_id, data=stage_data, partial=True)

        if not stage_couple.is_valid():
            return error_with_text(stage_couple.errors)

        stage_number = stage_couple.validated_data['order_stage_number']
        if OrderStageCouple.check_stage_number(stage_number, order.customer_manager.company,
                                               order_stage_id.pk):
            return error_with_text(f'order_stage_number_must_be_unique:{stage_number}')

        edit_stages[idx] = stage_couple

    for idx, stage_data in enumerate(add_stages):
        stage_serializer = OrderStageCoupleSerializer(data=stage_data)
        if not stage_serializer.is_valid():
            return error_with_text(stage_serializer.errors)

        stage_number = stage_serializer.validated_data['order_stage_number']
        if OrderStageCouple.check_stage_number(stage_number, order.customer_manager.company):
            return error_with_text(f'order_stage_number_must_be_unique:{stage_number}')

        add_stages[idx] = stage_serializer

    for s in delete_stages:
        s.delete()
    for s in edit_stages:
        s.save()
    for s in add_stages:
        s.save(order=order)


class EditOrderView(APIView):
    permission_classes = [IsActiveUser, IsCustomerManagerAccount]

    def post(self, request: Request):

        serializer = CustomerGetOrderByIdSerializer(
            data=request.data, customer_manager=request.user.customer_manager)
        if not serializer.is_valid():
            return error_with_text(serializer.errors)

        order: OrderModel = serializer.validated_data['order_id']
        if order.status != OrderStatus.unpublished:
            return error_with_text('You can edit only unpublished orders.')

        order_serializer = OrderSerializer(
            order, data=request.data, partial=True)
        if not order_serializer.is_valid():
            return error_with_text(order_serializer.errors)

        transportation_number = order_serializer.validated_data["transportation_number"]
        # check if transportation number unique (within company)
        if OrderModel.check_transportation_number(transportation_number, order.customer_manager.company, order.pk):
            return error_with_text('transportation_number_must_be_unique')

        stages_data = request.data.pop('stages', [])
        update_stages(customer_manager=request.user.customer_manager, order=order, stages_data=stages_data)
        order_serializer.save()

        orders = OrderModel.objects.filter(
            customer_manager__company=request.user.customer_manager.company
        )
        max_order_stage_number = OrderStageCouple.objects.filter(order__in=orders).aggregate(
            Max('order_stage_number'))['order_stage_number__max']
        return success_with_text({"order": order_serializer.data, "max_order_stage_number": max_order_stage_number})


class CancelOrderView(APIView):
    permission_classes = [IsActiveUser, IsCustomerManagerAccount]

    def post(self, request: Request):
        serializer = CustomerGetOrderByIdSerializer(
            data=request.data, customer_manager=request.user.customer_manager)
        if not serializer.is_valid():
            return error_with_text(serializer.errors)

        order: OrderModel = serializer.validated_data['order_id']
        order.make.cancelled(offer=order.offers.filter(
            status=OrderOfferStatus.accepted).order_by('price').first())

        #  Creating a copy of the order
        # order: OrderModel = serializer.validated_data['order_id']
        # if order.transporter_manager is not None:
        #     # create a copy of the order
        #     orig_order_pk = order.pk
        #     order.pk = None
        #     order.status = OrderStatus.cancelled
        #     order.save()
        #     order = OrderModel.objects.get(pk=orig_order_pk)
        #
        # order.make.cancelled()

        return success_with_text(OrderSerializer(order).data)


class UnpublishOrderView(APIView):
    permission_classes = [IsActiveUser, IsCustomerManagerAccount]

    def post(self, request: Request):
        serializer = CustomerGetOrderByIdSerializer(
            data=request.data, customer_manager=request.user.customer_manager)
        if not serializer.is_valid():
            return error_with_text(serializer.errors)

        order: OrderModel = serializer.validated_data['order_id']
        order.make.unpublished()

        return success_with_text(OrderSerializer(order).data)


class PublishOrderToView(APIView):
    permission_classes = [IsActiveUser, IsCustomerManagerAccount]

    def post(self, request: Request):
        serializer = PublishOrderToSerializer(
            data=request.data, customer_manager=request.user.customer_manager)
        if not serializer.is_valid():
            return error_with_text(serializer.errors)

        publish_to = request.data['publish_to']
        order: OrderModel = serializer.validated_data['order_id']

        if publish_to == OrderStatus.in_direct:
            direct_serializer = PublishToDirectSerializer(
                data=request.data, customer_manager=request.user.customer_manager)
            if not direct_serializer.is_valid():
                return error_with_text(direct_serializer.errors)
            transporter_manager = direct_serializer.validated_data['transporter_company_id'].get_manager(
            )
            if transporter_manager is None:
                return error_with_text("transporter_company has no manager")
            price = direct_serializer.validated_data['price']
            OrderOffer.objects.create(
                order=order, transporter_manager=transporter_manager, price=price)
        order.make.published_to(publish_to)
        return success_with_text(OrderSerializer(order).data)


class CompleteOrderView(APIView):
    permission_classes = [IsActiveUser, IsCustomerManagerAccount]

    def post(self, request: Request):
        serializer = CustomerGetOrderByIdSerializer(
            data=request.data, customer_manager=request.user.customer_manager)
        if not serializer.is_valid():
            return error_with_text(serializer.errors)

        order: OrderModel = serializer.validated_data['order_id']
        order.make.completed()

        return success_with_text(OrderSerializer(order).data)


class CancelOrderCompletionView(APIView):
    permission_classes = [IsActiveUser, IsCustomerManagerAccount]

    def post(self, request: Request):
        serializer = CustomerGetOrderByIdSerializer(
            data=request.data, customer_manager=request.user.customer_manager)
        if not serializer.is_valid():
            return error_with_text(serializer.errors)

        order: OrderModel = serializer.validated_data['order_id']
        order.make.cancel_completion()

        return success_with_text(OrderSerializer(order).data)
