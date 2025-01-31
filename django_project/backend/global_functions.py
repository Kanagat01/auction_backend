from phonenumbers import NumberParseException, PhoneNumber, PhoneNumberFormat
from smsaero import SmsAero, SmsAeroException, phonenumbers
from rest_framework.views import exception_handler
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework import status
from .settings import SMS_LOGIN, SMS_PASSWORD
import logging

logger = logging.getLogger("django")


def error_with_text(text):
    return Response({'status': 'error', 'message': text}, status=status.HTTP_400_BAD_REQUEST)


def success_with_text(text):
    return Response({'status': 'success', 'message': text}, status=status.HTTP_200_OK)


def send_sms(phone: str, message: str) -> dict:
    """
    Sends an SMS message

    Parameters:
    phone (int): The phone number to which the SMS message will be sent.
    message (str): The content of the SMS message to be sent.

    Returns:
    dict: A dictionary containing the response from the SmsAero API.
    """
    try:
        parsed_phone = phonenumbers.parse(phone)
        phone_number = int(phonenumbers.format_number(
            parsed_phone, PhoneNumberFormat.E164))
    except NumberParseException:
        raise SmsAeroException("Number must be a valid phone number")

    api = SmsAero(SMS_LOGIN, SMS_PASSWORD)
    response = api.send_sms(phone_number, message)
    logger.info(f"SMS sent to +{phone_number}: {message}")
    return response


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
