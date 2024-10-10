from django import forms
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.contrib import admin
from api_users.models import *

admin.site.register(ApplicationForRegistration)


@admin.register(Settings)
class SettingsAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        if Settings.objects.exists():
            return False
        return True

    def has_delete_permission(self, request, obj=None):
        return False

    def change_view(self, request, object_id=None, form_url='', extra_context=None):
        if not object_id and Settings.objects.exists():
            obj = Settings.objects.first()
            return HttpResponseRedirect(reverse('admin:api_users_settings_change', args=[obj.pk]))

        return super().change_view(request, object_id, form_url, extra_context)


class CompanyAdmin(admin.ModelAdmin):
    list_display = ['id', 'company_name', 'subscription_paid']
    list_filter = ['subscription_paid']


class TransporterCompanyForm(forms.ModelForm):
    class Meta:
        model = TransporterCompany
        fields = ['user', 'company_name', 'details',
                  'balance', 'subscription', 'subscription_paid']


@admin.register(TransporterCompany)
class TransporterCompanyAdmin(CompanyAdmin):
    form = TransporterCompanyForm


class CustomerCompanyForm(forms.ModelForm):
    allowed_transporter_companies = forms.ModelMultipleChoiceField(
        queryset=TransporterCompany.objects.all(), required=False, label=CustomerCompany._meta.get_field('allowed_transporter_companies').verbose_name)

    class Meta:
        model = CustomerCompany
        fields = ['user', 'company_name', 'details', 'allowed_transporter_companies',
                  'balance', 'subscription', 'subscription_paid']


@admin.register(CustomerCompany)
class CustomerCompanyAdmin(CompanyAdmin):
    form = CustomerCompanyForm


@admin.register(UserModel)
class UserModelAdmin(admin.ModelAdmin):
    list_display = ['id', 'full_name', 'username', 'user_type']
    search_fields = ['id', 'full_name', 'username']
    search_help_text = 'Ищите по: ID, полному имени, имени пользователя (email или номер телефона)'
    list_filter = ['user_type']


admin.site.register(CustomerManager)
admin.site.register(TransporterManager)
admin.site.register(DriverProfile)


class SubscriptionAdmin(admin.ModelAdmin):
    exclude = ('codename',)

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


admin.site.register(CustomerSubscription, SubscriptionAdmin)
admin.site.register(TransporterSubscription, SubscriptionAdmin)
