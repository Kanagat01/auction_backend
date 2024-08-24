from channels.db import database_sync_to_async
from backend.global_functions import BaseAuthorisedConsumer
from .serializers import *
from .models import *


class OrderConsumer(BaseAuthorisedConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.status = None

    def get_group_name(self):
        return f"user_orders_{self.user.id}"

    async def receive_json(self, data):
        '''
        Чтобы изменить статус {action: 'set_status', status: :OrderStatus}
        '''
        action = data.get("action")
        if action == "set_status":
            new_status = data.get("status")
            if new_status in OrderStatus.get_status_list(self.user.user_type):
                self.status: OrderStatus = new_status
            else:
                await self.send_json({"error": "incorrect_status"})

    async def add_or_update_order(self, event):
        order: OrderModel = await database_sync_to_async(
            OrderModel.objects.get
        )(id=int(event["order_id"]))
        if (self.status == order.status) or (self.status == OrderStatus.being_executed and order.status == OrderStatus.completed):
            if self.user.user_type in [UserTypes.CUSTOMER_COMPANY, UserTypes.CUSTOMER_MANAGER]:
                serializer_data = await database_sync_to_async(lambda: OrderSerializer(order).data)()
            else:
                serializer_data = await database_sync_to_async(
                    lambda: OrderSerializerForTransporter(
                        order, transporter_manager=order.transporter_manager).data
                )()
            await self.send_json({"add_or_update_order": serializer_data})

    async def remove_order(self, event):
        if self.status == event["order_status"]:
            await self.send_json({"remove_order": event["order_id"]})
