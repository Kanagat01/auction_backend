import json
import logging
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from api_auction.models import *
from api_auction.serializers import *
from api_notification.models import *
from api_notification.serializers import *

logger = logging.getLogger('websocket')


class BaseAuthorisedConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = None
        self.group_name = None
        self.status = None
        self.is_driver = False

    async def connect(self):
        self.user = self.scope["user"]
        self.is_driver = await database_sync_to_async(lambda: hasattr(self.user, 'driver_profile'))()
        if self.user.is_authenticated:
            self.group_name = f"user_{self.user.id}"
            await self.channel_layer.group_add(self.group_name, self.channel_name)
            await self.accept()
            logger.info(f"{self.user} connected")
            await self.send_json({"message": "connected"})
        else:
            await self.close()

    async def disconnect(self, close_code):
        if self.user.is_authenticated and self.group_name:
            logger.info(f"{self.user} disconnected")
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def send_json(self, data, logging_enabled=True):
        """Send a JSON serialized message."""
        text_data = json.dumps(data)
        if logging_enabled:
            logger.info(f"Send json to {self.user}: {text_data}")
        await self.send(text_data=text_data)

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            await self.receive_json(data)
        except json.JSONDecodeError:
            await self.send_json({"error": "Invalid JSON"})

    async def receive_json(self, data):
        '''
        Чтобы изменить статус {action: 'set_status', status: :OrderStatus}
        Чтобы создать геоточку {order_id: int, latitude: double, longitude: double}
        '''
        logger.info(f"Receive json from {self.user}: {data}")
        if self.is_driver:
            await self.create_geopoint(data)
            return

        action = data.get("action")
        if action == "set_status":
            new_status = data.get("status")
            if new_status in OrderStatus.get_status_list(self.user.user_type):
                self.status: OrderStatus = new_status
                await self.send_json({"status": new_status})
            else:
                await self.send_json({"error": "incorrect_status"})

    async def create_geopoint(self, data):
        try:
            order_id = int(data.get("order_id"))
        except Exception as ex:
            await self.send_json({"error": ex})
            return

        order = await database_sync_to_async(
            OrderModel.objects.get
        )(id=order_id)
        have_access = await database_sync_to_async(lambda: order.driver != self.user.driver_profile)()
        if have_access:
            await self.send_json({"error": "order isn't belong to you"})
            return

        if order.status != OrderStatus.being_executed:
            await self.send_json({"error": "order status isn't being executed"})
            return

        try:
            tracking_id = await database_sync_to_async(lambda: order.tracking.id)()
        except OrderModel.tracking.RelatedObjectDoesNotExist:
            tracking = await database_sync_to_async(OrderTracking.objects.create)(order=order)
            tracking_id = tracking.id

        serializer = OrderTrackingGeoPointSerializer(
            data={'tracking': tracking_id, **data})

        is_valid = await database_sync_to_async(serializer.is_valid)()
        if is_valid:
            await database_sync_to_async(serializer.save)()
            await self.send_json({"success": True})
        else:
            await self.send_json({"error": serializer.errors})

    async def send_notification(self, event):
        new_notification = await database_sync_to_async(
            Notification.objects.get)(id=int(event["notification_id"]))
        await self.send_json({"new_notification": NotificationSerializer(new_notification).data})

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
            logger.info(
                f"Send json to {self.user}: Order #{order.id} added or updated")
            await self.send_json({"add_or_update_order": serializer_data}, logging_enabled=False)

    async def remove_order(self, event):
        if self.status == event["order_status"]:
            await self.send_json({"remove_order": event["order_id"]})

    async def update_balance(self, event):
        new_balance = event["new_balance"]
        await self.send_json({"update_balance": new_balance})
