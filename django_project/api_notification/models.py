from django.db import models
from api_users.models.user import UserModel
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync


class Notification(models.Model):
    user = models.ForeignKey(
        UserModel, on_delete=models.CASCADE, related_name="notifications")
    title = models.CharField(max_length=200, verbose_name="Название")
    description = models.CharField(max_length=300, verbose_name="Описание")
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name="Создан в")

    class Meta:
        verbose_name = "Уведомление"
        verbose_name_plural = "Уведомления"

    def save(self, *args, **kwargs):
        super(Notification, self).save(*args, **kwargs)
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"user_{self.user.pk}", {
                "type": "send_notification",
                "notification_id": self.pk
            }
        )

    def __str__(self):
        return f"Уведомление #{self.pk}"
