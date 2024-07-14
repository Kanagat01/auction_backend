from backend.global_functions import success_with_text, error_with_text
from rest_framework.views import APIView
from rest_framework.request import Request
from api_notification.models import *
from api_notification.serializers import *
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync


class GetNotifications(APIView):
    def get(self, request: Request):
        return success_with_text(NotificationSerializer(request.user.notifications.all(), many=True).data)


class CreateNotification(APIView):
    permission_classes = ()

    def get(self, request: Request):
        user = UserModel.objects.get(email="customer_company@gmail.com")
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"user_{user.pk}", {
                "type": "send_notification",
                "notification_id": 58
            }
        )
        return success_with_text("ok")


class DeleteNotification(APIView):
    def post(self, request: Request):
        notification_id = request.data.get("notification_id")
        if not notification_id:
            return error_with_text("notification_id is required")
        try:
            notification = request.user.notifications.get(id=notification_id)
            notification.delete()
            return success_with_text("ok")
        except Notification.DoesNotExist:
            return error_with_text("notification not found")
