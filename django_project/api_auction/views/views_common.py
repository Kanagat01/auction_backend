import os
import subprocess
from datetime import datetime
from docxtpl import DocxTemplate
from django.http import HttpResponse
from django.db.models import Q, Exists, OuterRef, Subquery, Value, CharField
from django.db.models.functions import Concat
from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated

from api_auction.models import *
from api_auction.serializers import *
from api_users.models.user import UserModel, UserTypes
from api_users.permissions import *
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


class GetOrderPdf(APIView):
    permission_classes = [IsAuthenticated]

    @staticmethod
    def to_int(x):
        return int(x) if isinstance(x, float) and x.is_integer() else x

    @staticmethod
    def format_date(date: str, date_format="%Y-%m-%d", output_format="%d.%m.%Y"):
        return datetime.strptime(date, date_format).strftime(output_format)

    @staticmethod
    def format_time(time: str):
        return time[:-3]  # Убираем секунды

    @staticmethod
    def format_datetime(date: str, time_start: str, time_end: str):
        formatted_date = GetOrderPdf.format_date(date)
        formatted_time = f'{GetOrderPdf.format_time(time_start)}-{GetOrderPdf.format_time(time_end)}'
        return f'{formatted_date}\n{formatted_time}'

    def get_user_serializer(self, user, query_params):
        if user.user_type in [UserTypes.CUSTOMER_MANAGER, UserTypes.CUSTOMER_COMPANY]:
            manager = user.customer_manager if hasattr(
                user, "customer_manager") else user.customer_company.managers.first()
            return CustomerGetOrderByIdSerializer(data=query_params, customer_manager=manager)
        elif user.user_type in [UserTypes.TRANSPORTER_MANAGER, UserTypes.TRANSPORTER_COMPANY]:
            manager = user.transporter_manager if hasattr(
                user, "transporter_manager") else user.transporter_company.get_manager()
            return TransporterGetOrderByIdSerializer(data=query_params, transporter_manager=manager)
        return None

    def prepare_order_data(self, order_data, order):
        order_data.update({
            "transport_body_type": order.transport_body_type.name,
            "transport_load_type": order.transport_load_type.name,
            "transport_unload_type": order.transport_unload_type.name,
            "transport_body_width": self.to_int(order_data["transport_body_width"]),
            "transport_body_length": self.to_int(order_data["transport_body_length"]),
            "transport_body_height": self.to_int(order_data["transport_body_height"]),
            "stage_number_lst": ", ".join(str(x["order_stage_number"]) for x in order_data["stages"]),
            "application_type": self.get_application_type(order_data.get("application_type")),
        })

        assignment_datetime = None
        if order.status in [OrderStatus.being_executed, OrderStatus.completed]:
            assignment_datetime = order_data["offers"][0]["updated_at"]
        elif order.status == OrderStatus.in_direct:
            offer = order_data["offers"][0]
            assignment_datetime = offer["created_at"]
            order_data["transporter_manager"] = offer["transporter_manager"]

        if assignment_datetime:
            order_data["assignment_datetime"] = self.format_date(
                assignment_datetime, "%Y-%m-%dT%H:%M:%S.%f%z", "%d.%m.%Y %H:%M")

        if order.status == OrderStatus.in_direct and order_data["offers"]:
            offer = order_data["offers"][0]
            if offer["status"] == OrderOfferStatus.rejected:
                order_data[
                    "rejected_offer_text"] = f'Отказ Перевозчика от Заказа, {self.format_date(offer["updated_at"], "%Y-%m-%dT%H:%M:%S.%f%z", "%d.%m.%Y %H:%M")}'

        self.prepare_stages(order_data)

    @staticmethod
    def get_application_type(application_type):
        return {
            "in_auction": "Аукцион",
            "in_bidding": "Торги",
        }.get(application_type, "Прямой заказ" if application_type else None)

    def prepare_stages(self, order_data):
        for idx, stage in enumerate(order_data["stages"]):
            load_stage = stage["load_stage"]
            load_stage["datetime"] = self.format_datetime(
                load_stage["date"], load_stage["time_start"], load_stage["time_end"])

            unload_stage = stage["unload_stage"]
            unload_stage["datetime"] = self.format_datetime(
                unload_stage["date"], unload_stage["time_start"], unload_stage["time_end"])

            stage_data = [
                stage["order_stage_number"],
                load_stage,
                unload_stage,
                stage["cargo"],
                self.to_int(stage["weight"]),
                self.to_int(stage["volume"]),
            ]
            order_data["stages"][idx] = stage_data

    def generate_pdf(self, docx_file_path):
        pdf_file_path = docx_file_path.replace(".docx", ".pdf")
        subprocess.run(
            ['soffice', '--headless', '--convert-to', 'pdf', docx_file_path])
        return pdf_file_path

    def get(self, request: Request):
        user: UserModel = request.user
        serializer = self.get_user_serializer(user, request.query_params)

        if not serializer or not serializer.is_valid():
            return error_with_text(serializer.errors)

        order: OrderModel = serializer.validated_data["order_id"]
        order_data = OrderSerializer(order).data

        self.prepare_order_data(order_data, order)

        docx_file_path = f"order_{order.pk}.docx"
        template = DocxTemplate("api_auction/views/order_pdf_template.docx")
        template.render(order_data)
        template.save(docx_file_path)

        pdf_file_path = self.generate_pdf(docx_file_path)
        with open(pdf_file_path, 'rb') as pdf_file:
            pdf_content = pdf_file.read()

        os.remove(docx_file_path)
        os.remove(pdf_file_path)

        response = HttpResponse(pdf_content, content_type="application/pdf")
        return response
