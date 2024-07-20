from django.forms import model_to_dict
from django.db.models import OuterRef, Subquery, Q, Value, CharField
from django.db.models.functions import Concat
from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination

from api_auction.models import *
from api_auction.serializers import *
from api_notification.models import Notification, NotificationType
from api_users.models.user import UserModel, UserTypes
from api_users.permissions.customer_permissions import IsCustomerCompanyAccount, IsCustomerManagerAccount
from api_users.permissions.transporter_permissions import IsTransporterCompanyAccount, IsTransporterManagerAccount
from backend.global_functions import success_with_text, error_with_text


class PaginationClass(PageNumberPagination):
    page_size = 20


class GetOrdersView(APIView):
    permission_classes = [IsCustomerCompanyAccount | IsCustomerManagerAccount |
                          IsTransporterCompanyAccount | IsTransporterManagerAccount]

    def get(self, request: Request) -> Response:
        user: UserModel = request.user
        user_type: UserTypes = request.user.user_type

        status_lst = [OrderStatus.cancelled, OrderStatus.in_auction, OrderStatus.in_bidding,
                      OrderStatus.in_direct, OrderStatus.being_executed, OrderStatus.completed]
        if user_type in [UserTypes.CUSTOMER_COMPANY, UserTypes.CUSTOMER_MANAGER]:
            status_lst.append(OrderStatus.unpublished)

        status = request.query_params.get('status')
        if status not in status_lst:
            return error_with_text("invalid_order_status")
        if status == OrderStatus.being_executed:
            status_filter = Q(status=OrderStatus.being_executed) | Q(
                status=OrderStatus.completed)
        else:
            status_filter = Q(status=status)

        filter_kwargs = {}
        transportation_number = request.query_params.get(
            'transportation_number')
        if transportation_number and transportation_number.isdigit():
            filter_kwargs["transportation_number__icontains"] = transportation_number

        match (user_type):
            case UserTypes.CUSTOMER_MANAGER:
                filter_kwargs["customer_manager"] = user.customer_manager
            case UserTypes.CUSTOMER_COMPANY:
                filter_kwargs['customer_manager__company'] = user.customer_company
            case UserTypes.TRANSPORTER_MANAGER:
                filter_kwargs['customer_manager__company__in'] = user.transporter_manager.company.allowed_customer_companies.all()
            case UserTypes.TRANSPORTER_COMPANY:
                filter_kwargs['customer_manager__company__in'] = user.transporter_company.allowed_customer_companies.all()

        orders = OrderModel.objects.filter(status_filter, **filter_kwargs)
        city_from = request.query_params.get('city_from')

        if city_from:
            earliest_load_stage_subquery = OrderLoadStage.objects.filter(
                order_couple__order=OuterRef('pk')
            ).annotate(
                datetime=Concat('date', Value(
                    ' '), 'time_start', output_field=CharField())
            ).order_by('datetime').values('city')[:1]
            orders = orders.annotate(
                earliest_load_stage_city=Subquery(earliest_load_stage_subquery)
            ).filter(earliest_load_stage_city__icontains=city_from)

        city_to = request.query_params.get('city_to')
        if city_to:
            latest_unload_stage_subquery = OrderUnloadStage.objects.filter(
                order_couple__order=OuterRef('pk')
            ).annotate(
                datetime_concat=Concat('date', Value(
                    ' '), 'time_end', output_field=CharField())
            ).order_by('-datetime_concat').values('city')[:1]

            orders = orders.annotate(
                latest_unload_stage_city=Subquery(latest_unload_stage_subquery)
            ).filter(latest_unload_stage_city__icontains=city_to)

        paginator = PaginationClass()
        page = paginator.paginate_queryset(orders, request)

        pagination_data = {
            'pages_total': paginator.page.paginator.num_pages,
            'current_page': paginator.page.number
        }
        match (user_type):
            case UserTypes.CUSTOMER_COMPANY | UserTypes.CUSTOMER_MANAGER:
                result = OrderSerializer(page, many=True).data
            case UserTypes.TRANSPORTER_COMPANY:
                result = [
                    OrderSerializerForTransporter(
                        order,
                        for_bidding=status == OrderStatus.in_bidding,
                        transporter_manager=order.transporter_manager
                    ).data for order in page if order.transporter_manager is not None
                ]
            case UserTypes.TRANSPORTER_MANAGER:
                result = OrderSerializerForTransporter(
                    page,
                    many=True,
                    for_bidding=status == OrderStatus.in_bidding,
                    transporter_manager=user.transporter_manager
                ).data
        return success_with_text({'pagination': pagination_data, 'orders': result})


class PreCreateOrderView(APIView):
    permission_classes = [IsCustomerManagerAccount]

    def get(self, request: Request):
        # get names of all transport body types, load types, unload types
        transport_body_types = OrderTransportBodyType.objects.all()
        transport_load_types = OrderTransportLoadType.objects.all()
        transport_unload_types = OrderTransportUnloadType.objects.all()

        return success_with_text({
            'transport_body_types': OrderTransportBodyTypeSerializer(transport_body_types, many=True).data,
            'transport_load_types': OrderTransportLoadTypeSerializer(transport_load_types, many=True).data,
            'transport_unload_types': OrderTransportUnloadTypeSerializer(transport_unload_types, many=True).data,
        })


class CreateOrderView(APIView):
    permission_classes = [IsCustomerManagerAccount]

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
        return success_with_text(OrderSerializer(order).data)


class EditOrderView(APIView):
    permission_classes = [IsCustomerManagerAccount]

    def post(self, request: Request):

        serializer = CustomerGetOrderByIdSerializer(
            data=request.data, context={'request': request})
        if not serializer.is_valid():
            return error_with_text(serializer.errors)

        order: OrderModel = serializer.validated_data['order_id']
        if order.status != OrderStatus.unpublished:
            return error_with_text('You can edit only unpublished orders.')

        transportation_number = order.transportation_number
        # check if transportation number unique (within company)
        if OrderModel.check_transportation_number(transportation_number, order.customer_manager.company, order.pk):
            return error_with_text('transportation_number_must_be_unique')

        order_serializer = OrderSerializer(
            order, data=request.data, partial=True)
        if not order_serializer.is_valid():
            return error_with_text(order_serializer.errors)

        stages_data = request.data.pop('stages', [])
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
                data=stage_data, context={'request': request})
            if not serializer.is_valid():
                return error_with_text(serializer.errors)

            delete_stages[idx] = serializer.validated_data['order_stage_id']

        for idx, stage_data in enumerate(edit_stages):
            stage_data["order_stage_id"] = stage_data.pop("id")
            serializer = CustomerGetOrderCoupleSerializer(
                data=stage_data, context={'request': request})
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

        order.updated_at = timezone.now()
        order_serializer.save()

        return success_with_text(order_serializer.data)


class CancelOrderView(APIView):
    permission_classes = [IsCustomerManagerAccount]

    def post(self, request: Request):
        serializer = CustomerGetOrderByIdSerializer(
            data=request.data, context={'request': request})
        if not serializer.is_valid():
            return error_with_text(serializer.errors)

        order: OrderModel = serializer.validated_data['order_id']
        order.make.cancelled()

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
    permission_classes = [IsCustomerManagerAccount]

    def post(self, request: Request):
        serializer = CustomerGetOrderByIdSerializer(
            data=request.data, context={'request': request})
        if not serializer.is_valid():
            return error_with_text(serializer.errors)

        order: OrderModel = serializer.validated_data['order_id']
        order.make.unpublished()

        return success_with_text(OrderSerializer(order).data)


class PublishOrderToView(APIView):
    permission_classes = [IsCustomerManagerAccount]

    def post(self, request: Request):
        serializer = PublishOrderToSerializer(
            data=request.data, context={'request': request})
        if not serializer.is_valid():
            return error_with_text(serializer.errors)

        publish_to = request.data['publish_to']
        order: OrderModel = serializer.validated_data['order_id']

        if publish_to == OrderStatus.in_direct:
            direct_serializer = PublishToDirectSerializer(
                data=request.data, context={'request': request})
            if not direct_serializer.is_valid():
                return error_with_text(direct_serializer.errors)
            transporter_manager = direct_serializer.validated_data['transporter_company_id'].get_manager(
            )
            price = direct_serializer.validated_data['price']
            OrderOffer.objects.create(
                order=order, transporter_manager=transporter_manager, price=price)
            Notification.objects.create(
                user=transporter_manager.user,
                title=f"Вам назначен заказ",
                description=(
                    f"Вам назначена транспортировка №{order.transportation_number} "
                    f"заказчиком {order.customer_manager.company.company_name}. "
                    "Вы можете принять или отклонить предложение"
                ),
                type=NotificationType.NEW_ORDER_IN_DIRECT
            )
        order.make.published_to(publish_to)
        if publish_to != OrderStatus.in_direct:
            companies = order.customer_manager.company.allowed_transporter_companies.all()
            for company in companies:
                for manager in company.managers.all():
                    Notification.objects.create(
                        user=manager.user,
                        title=f"Новый заказ в {'в аукционе' if publish_to == OrderStatus.in_auction else 'в торгах'}",
                        description=(
                            f"Транспортировка №{order.transportation_number} добавлена "
                            f"{'в аукцион' if publish_to == OrderStatus.in_auction else 'в торги'}"
                        ),
                        type=(
                            NotificationType.NEW_ORDER_IN_AUCTION
                            if publish_to == OrderStatus.in_auction
                            else NotificationType.NEW_ORDER_IN_BIDDING
                        )
                    )
        return success_with_text(OrderSerializer(order).data)


class CompleteOrderView(APIView):
    permission_classes = [IsCustomerManagerAccount]

    def post(self, request: Request):
        serializer = CustomerGetOrderByIdSerializer(
            data=request.data, context={'request': request})
        if not serializer.is_valid():
            return error_with_text(serializer.errors)

        order: OrderModel = serializer.validated_data['order_id']
        order.make.completed()

        return success_with_text(OrderSerializer(order).data)
