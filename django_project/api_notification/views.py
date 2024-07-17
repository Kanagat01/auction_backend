from backend.global_functions import success_with_text, error_with_text
from rest_framework.views import APIView
from rest_framework.request import Request
from api_notification.models import *
from api_notification.serializers import *


class GetNotifications(APIView):
    def get(self, request: Request):
        return success_with_text(NotificationSerializer(request.user.notifications.all(), many=True).data)


class DeleteNotification(APIView):
    def post(self, request: Request):
        serializer = DeleteNotificationSerializer(data=request.data)
        if not serializer.is_valid():
            return error_with_text(serializer.errors)
        notification_id = serializer.validated_data["notification_id"]
        try:
            notification = request.user.notifications.get(id=notification_id)
            notification.delete()
            return success_with_text("ok")
        except Notification.DoesNotExist:
            return error_with_text("notification not found")
