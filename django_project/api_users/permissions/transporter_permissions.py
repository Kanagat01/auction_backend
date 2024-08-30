from rest_framework.permissions import IsAuthenticated
from api_users.models import UserTypes


class IsTransporterCompanyAccount(IsAuthenticated):
    def has_permission(self, request, view):
        is_authenticated = super().has_permission(request, view)
        if not is_authenticated:
            return False
        return request.user.user_type == UserTypes.TRANSPORTER_COMPANY


class IsTransporterManagerAccount(IsAuthenticated):
    def has_permission(self, request, view):
        is_authenticated = super().has_permission(request, view)
        if not is_authenticated:
            return False
        return request.user.user_type == UserTypes.TRANSPORTER_MANAGER
