from datetime import timedelta
from django.urls import reverse
from django.utils import timezone
from django.core.mail import send_mail
from django.contrib.auth import authenticate
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.authtoken.models import Token

from backend.settings import EMAIL_HOST_USER, REACT_RESET_PASSWORD_URL
from backend.global_functions import success_with_text, error_with_text
from api_users.serializers import *


class RegisterTransporterCompanyView(APIView):
    permission_classes = ()

    def post(self, request: Request):
        serializer = RegisterCompanySerializer(data=request.data)
        if not serializer.is_valid():
            return error_with_text(serializer.errors)

        user = UserModel.objects.create_user(
            email=serializer.validated_data['email'],
            username=serializer.validated_data['email'],
            user_type=UserTypes.TRANSPORTER_COMPANY,
            full_name=serializer.validated_data['full_name']
        )
        TransporterCompany.objects.create(user=user,
                                          company_name=serializer.validated_data['company_name'])

        user.set_password(serializer.validated_data['password'])
        user.save()

        token = Token.objects.create(user=user)
        return success_with_text({'token': token.key})


class RegisterCustomerCompanyView(APIView):
    permission_classes = ()

    def post(self, request: Request):
        serializer = RegisterCompanySerializer(data=request.data)
        if not serializer.is_valid():
            return error_with_text(serializer.errors)

        user = UserModel.objects.create_user(
            email=serializer.validated_data['email'],
            username=serializer.validated_data['email'],
            user_type=UserTypes.CUSTOMER_COMPANY,
            full_name=serializer.validated_data['full_name']
        )
        CustomerCompany.objects.create(user=user,
                                       company_name=serializer.validated_data['company_name'])

        user.set_password(serializer.validated_data['password'])
        user.save()

        token = Token.objects.create(user=user)
        return success_with_text({'token': token.key})


class Login(APIView):
    """
    Log in the user
    returns Token
    """
    permission_classes = ()

    def post(self, request: Request):
        serializer = LogInSerializer(data=request.data)

        if not serializer.is_valid():
            return error_with_text(serializer.errors)

        username = serializer.validated_data['username']
        password = serializer.validated_data['password']

        user: UserModel = authenticate(username=username, password=password)
        if user is None:
            return error_with_text('invalid_credentials')
        if user.user_type == UserTypes.DRIVER:
            return error_with_text('nice try)')

        # Deleting previous token
        Token.objects.filter(user=user).delete()
        token = Token.objects.create(user=user)
        return success_with_text({'token': token.key})


class PasswordResetView(APIView):
    permission_classes = ()

    def post(self, request: Request):
        serializer = PasswordResetSerializer(data=request.data)
        if not serializer.is_valid():
            return error_with_text(serializer.errors)

        email = serializer.validated_data['email']
        user = UserModel.objects.filter(email=email).first()
        if not user:
            return error_with_text("user_not_found")

        token_generator = PasswordResetTokenGenerator()
        token = token_generator.make_token(user)

        reset_objects = PasswordReset.objects.filter(token=token)
        for reset_obj in reset_objects:
            reset_obj.delete()
        reset = PasswordReset(email=email, token=token)
        reset.save()

        request.build_absolute_uri(
            reverse('password_reset_confirm', args=[token])
        )
        message = [
            "Вы сделали запрос на сброс пароля.",
            f"Нажмите на ссылку, чтобы сбросить свой пароль: {REACT_RESET_PASSWORD_URL + token}",
            "Ссылка будет недоступна через 24 часа.",
            "Если это были не вы, не переходите по ссылке"
        ]
        send_mail(
            'Запрос на сброс пароля',
            "\n".join(message),
            EMAIL_HOST_USER,
            [email],
        )
        return success_with_text('ok')


class PasswordResetConfirmView(APIView):
    permission_classes = ()

    def post(self, request: Request, token: str):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        if not serializer.is_valid():
            return error_with_text(serializer.errors)

        reset_obj = PasswordReset.objects.filter(token=token).first()
        if not reset_obj:
            return error_with_text('invalid_token')
        if timezone.now() > reset_obj.created_at + timedelta(days=1):
            reset_obj.delete()
            return error_with_text("token_expired")

        user = UserModel.objects.filter(email=reset_obj.email).first()
        if not user:
            return error_with_text('user_not_found')

        user.set_password(serializer.validated_data['new_password'])
        user.save()
        reset_obj.delete()

        Token.objects.filter(user=user).delete()
        token = Token.objects.create(user=user)
        return success_with_text({'token': token.key})
