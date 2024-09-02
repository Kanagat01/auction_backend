import json
import requests
from channels.generic.websocket import AsyncWebsocketConsumer
from rest_framework.views import exception_handler
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework import status
from .settings import SMS_LOGIN, SMS_PASSWORD


def error_with_text(text):
    return Response({'status': 'error', 'message': text}, status=status.HTTP_400_BAD_REQUEST)


def success_with_text(text):
    return Response({'status': 'success', 'message': text}, status=status.HTTP_200_OK)


def send_sms(number: str, text: str):
    url = f"https://{SMS_LOGIN}:{SMS_PASSWORD}@gate.smsaero.ru/v2/sms/send"
    params = {
        'number': number.replace("+", "").replace(" ", ""),
        'text': text,
        'sign': 'SMS Aero',
    }
    try:
        response = requests.get(url, params=params)
        data = response.json()
        if not data.get('success'):
            raise Exception(data.get('message'))

    except Exception as err:
        raise err


def all_read_only_serializer(cls):
    """
    make all fields of a serializer read only
    :param cls:
    :return:
    """

    def get_fields(self):
        fields = super(cls, self).get_fields()
        for field in fields.values():
            field.read_only = True
        return fields

    cls.get_fields = get_fields
    return cls


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if isinstance(exc, ValidationError):
        return error_with_text(exc.detail)

    return response


class BaseAuthorisedConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = None
        self.group_name = None

    async def connect(self):
        self.user = self.scope["user"]
        if self.user.is_authenticated:
            self.group_name = self.get_group_name()
            await self.channel_layer.group_add(self.group_name, self.channel_name)
            await self.accept()
            await self.send_json({"message": "connected"})
        else:
            await self.close()

    async def disconnect(self, close_code):
        if self.user.is_authenticated and self.group_name:
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def send_json(self, data):
        """Send a JSON serialized message."""
        await self.send(text_data=json.dumps(data))

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            await self.receive_json(data)
        except json.JSONDecodeError:
            await self.send_json({"error": "Invalid JSON"})

    async def receive_json(self, data):
        """Override this method in the child class to handle messages."""
        raise NotImplementedError(
            "You must override receive_json() in your child class")

    def get_group_name(self):
        """Override this method in the child class to customize the group name."""
        raise NotImplementedError(
            "You must override the get_group_name() method in your child class")
