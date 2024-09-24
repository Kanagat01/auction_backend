import requests
from rest_framework.views import exception_handler
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework import status
from .settings import SMS_LOGIN, SMS_PASSWORD


def error_with_text(text):
    return Response({'status': 'error', 'message': text}, status=status.HTTP_400_BAD_REQUEST)


def success_with_text(text):
    return Response({'status': 'success', 'message': text}, status=status.HTTP_200_OK)


def send_sms(phone_number: str, code: str):
    phone_number = phone_number.replace("+", "")
    try:
        request_url = f'https://{SMS_LOGIN}:{SMS_PASSWORD}@gate.smsaero.ru/v2/sms/send/?number={phone_number}&sign=SMS Aero&text=Ваш код подтверждения в Cargonika: {code}'
        response = requests.get(request_url, timeout=20)
        return response.json()
    except Exception as e:
        print('Error:', str(e))
    return {}


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
