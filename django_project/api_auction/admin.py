from django.contrib import admin
from .models import *


admin.site.register(OrderTracking)
admin.site.register(OrderTrackingGeoPoint)
admin.site.register(OrderOffer)
admin.site.register(OrderLoadStage)
admin.site.register(OrderUnloadStage)


@admin.register(OrderModel)
class OrderAdmin(admin.ModelAdmin):
    class OrderStageCoupleInlines(admin.TabularInline):
        model = OrderStageCouple
        extra = 0

    class DocumentInlines(admin.TabularInline):
        model = OrderDocument
        extra = 0

    list_display = ['id', 'transportation_number', 'customer_manager', 'transporter_manager',
                    'driver', 'status']
    search_fields = [
        'id', 'transportation_number',
        # Поиск по имени менеджера
        'customer_manager__user__full_name', 'transporter_manager__user__full_name',
        # Поиск по имени компании
        'customer_manager__company__company_name', 'transporter_manager__company__company_name'
    ]
    search_help_text = 'Ищите по: ID, номеру транспортировки, имени менеджера или названию компании'
    list_filter = ['status']
    inlines = [OrderStageCoupleInlines, DocumentInlines]


@admin.register(OrderStageCouple)
class OrderStageCoupleAdmin(admin.ModelAdmin):
    list_display = ['id', 'order', 'created_at', 'order_stage_number']
    search_fields = ['id', 'order__id', 'order_stage_number']
    search_help_text = 'Ищите по: ID поставки, ID заказа или по номеру поставки'


@admin.register(OrderTransportBodyType)
class OrderTransportBodyTypeAdmin(admin.ModelAdmin):
    list_display = ['id', 'name']
    search_fields = ['id', 'name']
    search_help_text = 'Ищите по: ID или названию'


@admin.register(OrderTransportLoadType)
class OrderTransportLoadTypeAdmin(admin.ModelAdmin):
    list_display = ['id', 'name']
    search_fields = ['id', 'name']
    search_help_text = 'Ищите по: ID или названию'


@admin.register(OrderTransportUnloadType)
class OrderTransportUnloadTypeAdmin(admin.ModelAdmin):
    list_display = ['id', 'name']
    search_fields = ['id', 'name']
    search_help_text = 'Ищите по: ID или названию'
