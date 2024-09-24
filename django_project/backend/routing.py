from django.urls import re_path
from backend.base_consumer import BaseAuthorisedConsumer

websocket_urlpatterns = [
    re_path(r"api/ws/general/", BaseAuthorisedConsumer.as_asgi()),
]
