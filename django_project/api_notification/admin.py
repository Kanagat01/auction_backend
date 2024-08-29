from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import *


class NotificationTypeFilter(admin.SimpleListFilter):
    title = _('Notification type')
    parameter_name = 'type'

    def lookups(self, request, model_admin):
        return [(choice[0], choice[1]) for choice in NotificationType.CHOICES]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(type=self.value())
        return queryset


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'title', 'type']
    list_filter = [NotificationTypeFilter]  # Добавляем фильтр здесь
