from django.db import models
from api_users.models.user import UserModel
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync


class NotificationType:
    INFO = 'info'
    NEW_ORDER_IN_AUCTION = 'new_order_in_auction'
    NEW_ORDER_IN_BIDDING = 'new_order_in_bidding'
    NEW_ORDER_IN_DIRECT = 'new_order_in_direct'
    NEW_ORDER_BEING_EXECUTED = 'new_order_being_executed'
    ORDER_CANCELLED = 'order_cancelled'
    POPUP_NOTIFICATION = 'popup_notification'

    CHOICES = [
        (INFO, 'Информационная'),
        (NEW_ORDER_IN_AUCTION, 'Новый заказ в аукционе'),
        (NEW_ORDER_IN_BIDDING, 'Новый заказ в торгах'),
        (NEW_ORDER_IN_DIRECT, 'Новый заказ назначен напрямую'),
        (NEW_ORDER_BEING_EXECUTED, 'Новый заказ принят в исполнение'),
        (ORDER_CANCELLED, 'Заказ отменен'),
        (POPUP_NOTIFICATION, 'Всплывающее уведомление'),
    ]


class Notification(models.Model):
    user = models.ForeignKey(
        UserModel, on_delete=models.CASCADE, related_name="notifications")
    title = models.CharField(max_length=200, verbose_name="Название")
    description = models.TextField(max_length=500, verbose_name="Описание")
    type = models.CharField(
        max_length=24, choices=NotificationType.CHOICES, verbose_name="Тип")
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name="Создан в")

    class Meta:
        verbose_name = "Уведомление"
        verbose_name_plural = "Уведомления"
        ordering = ["created_at"]

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"user_{self.user.pk}", {
                "type": "send_notification",
                "notification_id": self.pk
            }
        )

    def __str__(self):
        return f"Уведомление #{self.pk}"
