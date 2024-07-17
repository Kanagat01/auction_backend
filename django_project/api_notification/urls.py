from django.urls import path
from .views import *

urlpatterns = [
    path("get_notifications/", GetNotifications.as_view()),
    path("delete_notification/", DeleteNotification.as_view()),
]
