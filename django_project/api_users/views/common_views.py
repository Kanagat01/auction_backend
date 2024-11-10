from backend.global_functions import success_with_text, error_with_text
from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.permissions import IsAuthenticated
from rest_framework.authtoken.models import Token
from api_users.permissions import IsCustomerCompanyAccount, IsTransporterCompanyAccount
from api_users.serializers import *
from api_users.models import *


class ValidateToken(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return success_with_text("ok")


class GetSettings(APIView):
    permission_classes = []

    def get(self, request):
        settings = Settings.objects.first()
        return success_with_text(SettingsSerializer(settings).data if settings else {})


class GetLandingData(APIView):
    permission_classes = []

    def get(self, request):
        settings = Settings.objects.first()
        response = {}
        response["settings"] = SettingsSerializer(
            settings).data if settings else {}

        subscriptions = CustomerSubscription.objects.all()
        response["subscriptions"] = CustomerSubscriptionSerializer(
            subscriptions, many=True).data
        return success_with_text(response)


class CreateApplicationForRegistration(APIView):
    permission_classes = []

    def post(self, request):
        serializer = ApplicationForRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return success_with_text("ok")
        return error_with_text(serializer.errors)


class GetUser(APIView):
    """
    Get user info
    """

    def get(self, request: Request):
        instance = request.user
        profile = {}
        if instance.user_type == UserTypes.CUSTOMER_COMPANY:
            profile = CustomerCompanySerializer(
                instance.customer_company).data
        elif instance.user_type == UserTypes.CUSTOMER_MANAGER:
            profile = CustomerManagerSerializer(
                instance.customer_manager).data
        elif instance.user_type == UserTypes.TRANSPORTER_COMPANY:
            profile = TransporterCompanySerializer(
                instance.transporter_company).data
        elif instance.user_type == UserTypes.TRANSPORTER_MANAGER:
            profile = TransporterManagerSerializer(
                instance.transporter_manager).data
        elif instance.user_type == UserTypes.DRIVER:
            return success_with_text(DriverProfileSerializer(instance.driver_profile).data)
        else:
            return error_with_text('user_not_found')

        return success_with_text(profile)


class EditUser(APIView):
    """
    Edit user info
    """

    def post(self, request: Request):
        instance: UserModel = request.user
        from_manager = instance.user_type in [
            UserTypes.CUSTOMER_MANAGER, UserTypes.TRANSPORTER_MANAGER]
        serializer = EditUserSerializer(
            data=request.data, from_manager=from_manager)
        if not serializer.is_valid():
            return error_with_text(serializer.errors)

        if not from_manager:
            if instance.user_type == UserTypes.CUSTOMER_COMPANY:
                company = CustomerCompany.objects.get(user=instance)
            else:
                company = TransporterCompany.objects.get(user=instance)

            company_name = serializer.validated_data["company_name"]
            if company_name:
                company.company_name = company_name

            details = serializer.validated_data["details"]
            if details:
                company.details = details
            company.save()

        instance.username = serializer.validated_data["email"]
        for key, value in serializer.validated_data.items():
            setattr(instance, key, value)
        instance.save()
        return success_with_text("ok")


class ChangePassword(APIView):
    def post(self, request: Request):
        user: UserModel = request.user
        serializer = ChangePasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return error_with_text(serializer.errors)

        data = serializer.validated_data
        if not user.check_password(data["old_password"]):
            return error_with_text("wrong_password")
        elif data["new_password"] != data["repeat_password"]:
            return error_with_text("passwords_do_not_match")

        user.set_password(data["new_password"])
        user.save()

        Token.objects.filter(user=user).delete()
        token = Token.objects.create(user=user)
        return success_with_text({'token': token.key})


class RegisterManagerForCompany(APIView):
    permission_classes = [IsCustomerCompanyAccount |
                          IsTransporterCompanyAccount]

    def post(self, request: Request):
        serializer = RegisterManagerSerializer(data=request.data)
        if not serializer.is_valid():
            return error_with_text(serializer.errors)

        email = serializer.validated_data['email']
        password = serializer.validated_data['password']
        full_name = serializer.validated_data['full_name']
        user_type = UserTypes.CUSTOMER_MANAGER if request.user.user_type == UserTypes.CUSTOMER_COMPANY else UserTypes.TRANSPORTER_MANAGER

        user = UserModel.objects.create_user(
            email=email,
            username=email,
            user_type=user_type,
            full_name=full_name
        )
        print('Retgistering manager with paswd:', password)
        if user.user_type == UserTypes.CUSTOMER_MANAGER:
            ins = CustomerManager.objects.create(
                user=user, company=request.user.customer_company)
            user.set_password(password)
            user.save()
            return success_with_text(CustomerManagerSerializer(ins, from_company=True).data)
        else:
            ins = TransporterManager.objects.create(
                user=user, company=request.user.transporter_company)
            user.set_password(password)
            user.save()
            return success_with_text(TransporterManagerSerializer(ins, from_company=True).data)


class EditManager(APIView):
    permission_classes = [IsCustomerCompanyAccount |
                          IsTransporterCompanyAccount]

    def post(self, request: Request):
        serializer = EditManagerSerializer(
            data=request.data, user=request.user)
        if not serializer.is_valid():
            return error_with_text(serializer.errors)

        manager = serializer.validated_data["manager_id"]
        user: UserModel = manager.user
        user.email = serializer.validated_data['email']
        user.full_name = serializer.validated_data['full_name']
        user.save()
        if user.user_type == UserTypes.CUSTOMER_MANAGER:
            return success_with_text(CustomerManagerSerializer(manager, from_company=True).data)
        else:
            return success_with_text(TransporterManagerSerializer(manager, from_company=True).data)


class ChangeSubscription(APIView):
    permission_classes = [IsCustomerCompanyAccount |
                          IsTransporterCompanyAccount]

    def post(self, request: Request):
        user: UserModel = request.user
        serializer = ChangeSubscriptionSerializer(
            data=request.data, context={'user_type': user.user_type})
        if not serializer.is_valid():
            return error_with_text(serializer.errors)

        is_customer = user.user_type == UserTypes.CUSTOMER_COMPANY
        subscription: Subscription = serializer.validated_data["subscription_id"]
        company: BaseCompany = user.customer_company if is_customer else user.transporter_company
        if company.subscription_paid:
            price_diff = subscription.price - company.subscription.price
            if price_diff > 0:
                if company.balance >= price_diff:
                    company.balance -= price_diff
                else:
                    return error_with_text(f"insufficient_funds:{price_diff - company.balance}")
        company.subscription = subscription
        company.save()

        if is_customer:
            return success_with_text(CustomerCompanySerializer(company).data)
        return success_with_text(TransporterCompanySerializer(company).data)
