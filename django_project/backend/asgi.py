import os
from urllib.parse import parse_qs
from django.core.asgi import get_asgi_application
from channels.db import database_sync_to_async
from channels.routing import ProtocolTypeRouter, URLRouter


class QueryAuthMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        query_string = scope['query_string'].decode()
        query_params = parse_qs(query_string)
        token = query_params.get('token')
        scope['user'] = await get_user(token[0] if token else "")
        return await self.app(scope, receive, send)


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django_asgi_app = get_asgi_application()

from .routing import websocket_urlpatterns

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": QueryAuthMiddleware(
            URLRouter(websocket_urlpatterns)
        ),
})


@database_sync_to_async
def get_user(token):
    from django.contrib.auth.models import AnonymousUser
    from rest_framework.authtoken.models import Token
    try:
        token = Token.objects.get(key=token)
        return token.user
    except Token.DoesNotExist:
        return AnonymousUser()
