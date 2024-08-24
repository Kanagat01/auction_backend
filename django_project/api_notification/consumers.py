from channels.db import database_sync_to_async
from backend.global_functions import BaseAuthorisedConsumer
from .serializers import *
from .models import *


class NotificationConsumer(BaseAuthorisedConsumer):
    def get_group_name(self):
        return f"user_notifications_{self.user.id}"

    # implemented in order to avoid NotImplementedException
    async def receive_json(self, data):
        pass

    async def send_notification(self, event):
        new_notification = await database_sync_to_async(
            Notification.objects.get)(id=int(event["notification_id"]))
        await self.send_json({"new_notification": NotificationSerializer(new_notification).data})
