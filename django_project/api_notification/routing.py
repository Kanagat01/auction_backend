from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r"api/ws/notifications/", consumers.NotificationConsumer.as_asgi()),
]
