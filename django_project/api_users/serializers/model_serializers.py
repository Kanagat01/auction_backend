from api_users.models import *
from rest_framework import serializers


class CustomerSubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerSubscription
        fields = '__all__'


class TransporterSubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = TransporterSubscription
        fields = '__all__'


class SettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Settings
        fields = '__all__'


class ApplicationForRegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApplicationForRegistration
        fields = '__all__'


class UserModelSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(source='id', read_only=True)

    class Meta:
        model = UserModel
        fields = ['user_id', 'email', 'user_type', 'full_name']


class CustomerCompanySerializer(serializers.ModelSerializer):
    customer_company_id = serializers.IntegerField(source='id', read_only=True)
    managers = serializers.SerializerMethodField()
    user = UserModelSerializer()
    subscription = CustomerSubscriptionSerializer()
    allowed_transporter_companies = serializers.SerializerMethodField()
    subscriptions_list = serializers.SerializerMethodField()

    def __init__(self, *args, from_manager=False, **kwargs):
        super().__init__(*args, **kwargs)
        if from_manager:
            self.fields.pop('allowed_transporter_companies')
            self.fields.pop('managers')
            self.fields.pop('user')

    class Meta:
        model = CustomerCompany
        exclude = ['id']

    def get_managers(self, instance):
        if self.context.get('from_manager'):
            return None
        return CustomerManagerSerializer(instance.managers.all(), many=True, from_company=True).data

    def get_allowed_transporter_companies(self, instance):
        return TransporterCompanySerializer(instance.allowed_transporter_companies.all(), many=True,
                                            from_manager=True).data

    def get_subscriptions_list(self, instance):
        return CustomerSubscriptionSerializer(CustomerSubscription.objects.all(), many=True).data


class CustomerManagerSerializer(serializers.ModelSerializer):
    user = UserModelSerializer()
    customer_manager_id = serializers.IntegerField(source='id', read_only=True)
    company = CustomerCompanySerializer(from_manager=True)
    allowed_transporter_companies = serializers.SerializerMethodField()

    def __init__(self, *args, from_company=False, **kwargs):
        super().__init__(*args, **kwargs)
        if from_company:
            self.fields.pop('company')

    class Meta:
        model = CustomerManager
        exclude = ['id']

    def get_allowed_transporter_companies(self, instance):
        return TransporterCompanySerializer(instance.company.allowed_transporter_companies.all(), many=True,
                                            from_manager=True).data


class TransporterCompanySerializer(serializers.ModelSerializer):
    user = UserModelSerializer()
    managers = serializers.SerializerMethodField()
    transporter_company_id = serializers.IntegerField(
        source='id', read_only=True)
    subscription = TransporterSubscriptionSerializer()
    subscriptions_list = serializers.SerializerMethodField()

    def __init__(self, *args, from_manager=False, **kwargs):
        super().__init__(*args, **kwargs)
        if from_manager:
            self.fields.pop('managers')
            self.fields.pop('user')

    class Meta:
        model = TransporterCompany
        exclude = ['id']

    def get_managers(self, instance):
        if self.context.get('from_manager'):
            return None
        return TransporterManagerSerializer(instance.managers.all(), many=True, from_company=True).data

    def get_subscriptions_list(self, instance):
        return TransporterSubscriptionSerializer(TransporterSubscription.objects.all(), many=True).data


class TransporterManagerSerializer(serializers.ModelSerializer):
    user = UserModelSerializer()
    company = TransporterCompanySerializer(from_manager=True)
    transporter_manager_id = serializers.IntegerField(
        source='id', read_only=True)

    def __init__(self, *args, from_company=False, **kwargs):
        super().__init__(*args, **kwargs)
        if from_company:
            self.fields.pop('company')

    class Meta:
        model = TransporterManager
        exclude = ['id']


class DriverProfileSerializer(serializers.ModelSerializer):
    driver_id = serializers.IntegerField(source='id', read_only=True)
    user = UserModelSerializer()

    class Meta:
        model = DriverProfile
        exclude = ['id']
