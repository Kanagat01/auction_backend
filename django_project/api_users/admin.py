from django.urls import reverse
from django.http import HttpResponseRedirect
from django.contrib import admin
from api_users.models import *


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


admin.site.register(UserModel)
admin.site.register(CustomerCompany)
admin.site.register(CustomerManager)
admin.site.register(TransporterCompany)
admin.site.register(TransporterManager)
admin.site.register(DriverProfile)


class SubscriptionAdmin(admin.ModelAdmin):
    exclude = ('codename',)

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(CustomerSubscription)
class CustomerSubscriptionAdmin(SubscriptionAdmin, admin.ModelAdmin):
    pass


@admin.register(TransporterSubscription)
class TransporterSubscriptionAdmin(SubscriptionAdmin, admin.ModelAdmin):
    pass
