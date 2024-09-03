from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import *


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'title', 'type']
    list_filter = ['type']
