from django.db.models import Q, Exists, OuterRef
from django.db.models import Q, OuterRef, Subquery,  Value, CharField, Exists, OuterRef
from django.db.models.functions import Concat
from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination

from api_auction.models import *
from api_auction.serializers import *
from api_users.models.user import UserModel, UserTypes
from api_users.permissions.customer_permissions import IsCustomerCompanyAccount, IsCustomerManagerAccount
from api_users.permissions.transporter_permissions import IsTransporterCompanyAccount, IsTransporterManagerAccount
from backend.global_functions import success_with_text, error_with_text


class PaginationClass(PageNumberPagination):
    page_size = 20


class FindCargoView(APIView):
    permission_classes = ()

    def get(self, request, transportation_number: int, machine_number: str):
        try:
            driver = DriverProfile.objects.get(machine_number=machine_number)
            order = OrderModel.objects.get(
                transportation_number=transportation_number, driver=driver)
            if order.customer_manager.company.subscription.codename != "all_functionality_and_find_cargo":
                return error_with_text("service is not available with current company subscription")
            return success_with_text(OrderSerializer(order, for_order_viewer=(not request.user.is_authenticated)).data)
        except DriverProfile.DoesNotExist:
            return error_with_text("driver_not_found")
        except OrderModel.DoesNotExist:
            return error_with_text("order_not_found")


class GetOrdersView(APIView):
    permission_classes = [IsCustomerCompanyAccount | IsCustomerManagerAccount |
                          IsTransporterCompanyAccount | IsTransporterManagerAccount]

    def get(self, request: Request) -> Response:
        user = request.user
        user_type = user.user_type

        status_lst = OrderStatus.get_status_list(user_type)
        status = request.query_params.get('status')
        if status not in status_lst:
            return error_with_text("invalid_order_status")

        status_filter = self.get_status_filter(status)
        filter_kwargs = self.get_filter_kwargs(
            request, user, user_type, status)
        orders = self.get_orders(
            status, filter_kwargs, user, user_type, status_filter)
        orders = self.apply_city_filters(request, orders)

        page, pagination_data = self.get_paginated_response(request, orders)

        result = self.serialize_orders(page, user, status)
        return success_with_text({
            'pagination': pagination_data,
            'orders': result,
            "pre_create_order": self.get_pre_create_order_data()
        })

    def get_status_filter(self, status):
        if status == OrderStatus.being_executed:
            return Q(status=OrderStatus.being_executed) | Q(status=OrderStatus.completed)
        return Q(status=status)

    def get_filter_kwargs(self, request, user, user_type, status):
        filter_kwargs = {}
        transportation_number = request.query_params.get(
            'transportation_number')
        if transportation_number and transportation_number.isdigit():
            filter_kwargs["transportation_number__icontains"] = transportation_number

        if user_type in [UserTypes.CUSTOMER_MANAGER, UserTypes.CUSTOMER_COMPANY]:
            company = user.customer_manager.company if user_type == UserTypes.CUSTOMER_MANAGER else user.customer_company
            filter_kwargs["customer_manager__company"] = company
        else:
            if user_type == UserTypes.TRANSPORTER_MANAGER:
                company = user.transporter_manager.company
            else:
                company = user.transporter_company
        
            if status in [OrderStatus.in_auction, OrderStatus.in_bidding]:
                filter_kwargs['customer_manager__company__in'] = company.allowed_customer_companies.all(
                )
            elif status in [OrderStatus.cancelled, OrderStatus.being_executed]:
                filter_kwargs['transporter_manager__company'] = company

        return filter_kwargs

    def get_orders(self, status, filter_kwargs, user, user_type, status_filter):
        if status == OrderStatus.in_direct and user_type in [UserTypes.TRANSPORTER_COMPANY, UserTypes.TRANSPORTER_MANAGER]:
            return self.get_direct_orders(filter_kwargs, user, user_type, status_filter)
        return OrderModel.objects.filter(status_filter, **filter_kwargs)

    def get_direct_orders(self, filter_kwargs, user, user_type, status_filter):
        if user_type == UserTypes.TRANSPORTER_MANAGER:
            company = user.transporter_manager.company
        else:
            company = user.transporter_company
        manager_filter = {"transporter_manager__company": company}
        
        return OrderModel.objects.annotate(
            has_offer=Exists(
                OrderOffer.objects.filter(
                    order=OuterRef('pk'), status=OrderOfferStatus.none, **manager_filter)
            )
        ).filter(status_filter, **filter_kwargs, has_offer=True)


    def apply_city_filters(self, request, orders):
        city_from = request.query_params.get('city_from')
        if city_from:
            earliest_load_stage_subquery = OrderLoadStage.objects.filter(
                order_couple__order=OuterRef('pk')
            ).annotate(
                datetime=Concat('date', Value(' '), 'time_start',
                                output_field=CharField())
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

        return orders

    def get_paginated_response(self, request, orders):
        paginator = PaginationClass()
        page = paginator.paginate_queryset(orders, request)
        pagination_data = {
            'pages_total': paginator.page.paginator.num_pages,
            'current_page': paginator.page.number
        }
        return page, pagination_data

    def get_pre_create_order_data(self):
        transport_body_types = OrderTransportBodyType.objects.all()
        transport_load_types = OrderTransportLoadType.objects.all()
        transport_unload_types = OrderTransportUnloadType.objects.all()
        return {
            'transport_body_types': OrderTransportBodyTypeSerializer(transport_body_types, many=True).data,
            'transport_load_types': OrderTransportLoadTypeSerializer(transport_load_types, many=True).data,
            'transport_unload_types': OrderTransportUnloadTypeSerializer(transport_unload_types, many=True).data,
        }

    def serialize_orders(self, page, user: UserModel, status):
        if user.user_type in [UserTypes.CUSTOMER_COMPANY, UserTypes.CUSTOMER_MANAGER]:
            return OrderSerializer(page, many=True).data
        elif user.user_type == UserTypes.TRANSPORTER_COMPANY:
            transporter_manager = user.transporter_company.get_manager()
            return [
                OrderSerializerForTransporter(
                    order,
                    for_bidding=status == OrderStatus.in_bidding,
                    transporter_manager=transporter_manager
                ).data for order in page if transporter_manager is not None
            ]
        else:
            return OrderSerializerForTransporter(
                page,
                many=True,
                for_bidding=status == OrderStatus.in_bidding,
                transporter_manager=user.transporter_manager
            ).data
