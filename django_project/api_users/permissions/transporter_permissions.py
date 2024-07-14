from api_users.models import UserModel, UserTypes
from api_users.models.subscriptions import CustomerSubscriptions
from api_users.permissions.common_permissions import IsAuthenticatedWithBlocked


class IsTransporterCompanyAccount(IsAuthenticatedWithBlocked):
    def has_permission(self, request, view):
        is_authenticated = super().has_permission(request, view)
        if not is_authenticated:
            return False
        return request.user.user_type == UserTypes.TRANSPORTER_COMPANY


class IsTransporterManagerAccount(IsAuthenticatedWithBlocked):
    def has_permission(self, request, view):
        is_authenticated = super().has_permission(request, view)
        if not is_authenticated:
            return False
        return request.user.user_type == UserTypes.TRANSPORTER_MANAGER
