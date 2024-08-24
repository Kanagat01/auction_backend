from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r"api/ws/orders/", consumers.OrderConsumer.as_asgi()),
]
