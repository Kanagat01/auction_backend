from rest_framework import serializers
from api_notification.models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        exclude = ["user"]

class DeleteNotificationSerializer(serializers.Serializer):
    notification_id = serializers.IntegerField()