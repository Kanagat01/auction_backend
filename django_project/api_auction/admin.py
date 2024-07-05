from django.contrib import admin
from .models import *


admin.site.register(OrderTracking)
admin.site.register(OrderTrackingGeoPoint)
admin.site.register(OrderOffer)


@admin.register(OrderModel)
class OrderAdmin(admin.ModelAdmin):
    class OrderStageCoupleInlines(admin.TabularInline):
        model = OrderStageCouple
        extra = 0

    class DocumentInlines(admin.TabularInline):
        model = OrderDocument
        extra = 0

    list_display = ['id', 'customer_manager', 'transporter_manager',
                    'created_at', 'updated_at', 'start_price']
    search_fields = ['id', 'customer_manager__user__username',
                     'transporter_manager__user__username']
    inlines = [OrderStageCoupleInlines, DocumentInlines]


@admin.register(OrderStageCouple)
class OrderStageCoupleAdmin(admin.ModelAdmin):
    list_display = ['id', 'order', 'created_at', 'order_stage_number']
    search_fields = ['id', 'order__id', 'order_stage_number']


@admin.register(OrderTransportBodyType)
class OrderTransportBodyTypeAdmin(admin.ModelAdmin):
    list_display = ['id', 'name']
    search_fields = ['id', 'name']


@admin.register(OrderTransportLoadType)
class OrderTransportLoadTypeAdmin(admin.ModelAdmin):
    list_display = ['id', 'name']
    search_fields = ['id', 'name']


@admin.register(OrderTransportUnloadType)
class OrderTransportUnloadTypeAdmin(admin.ModelAdmin):
    list_display = ['id', 'name']
    search_fields = ['id', 'name']
