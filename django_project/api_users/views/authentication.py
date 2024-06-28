from django.contrib.auth import authenticate, password_validation
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.authtoken.models import Token

from backend.global_functions import success_with_text, error_with_text
from api_users.serializers import *


# Create your views here.

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

        username = serializer.validated_data['email']
        password = serializer.validated_data['password']

        user: UserModel = authenticate(username=username, password=password)
        if user is None:
            return error_with_text('invalid_credentials')
        if user.blocked:
            return error_with_text('user_blocked')

        # Deleting previous token
        Token.objects.filter(user=user).delete()
        token = Token.objects.create(user=user)
        return success_with_text({'token': token.key})



