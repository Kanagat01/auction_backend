from django.contrib import admin
from api_users.models import *


# Register your models here.
@admin.register(UserModel)
class UserModelAdmin(admin.ModelAdmin):
    pass


@admin.register(CustomerCompany)
class CustomerCompanyAdmin(admin.ModelAdmin):
    pass


@admin.register(CustomerManager)
class CustomerManagerAdmin(admin.ModelAdmin):
    pass


@admin.register(TransporterCompany)
class TransporterCompanyAdmin(admin.ModelAdmin):
    pass


@admin.register(TransporterManager)
class TransporterManagerAdmin(admin.ModelAdmin):
    pass


@admin.register(DriverProfile)
class DriverProfileAdmin(admin.ModelAdmin):
    pass


@admin.register(OrderViewer)
class OrderViewerAdmin(admin.ModelAdmin):
    pass

