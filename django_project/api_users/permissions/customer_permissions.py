from api_users.models import UserTypes
from api_users.permissions.common_permissions import IsAuthenticatedWithBlocked


class IsCustomerCompanyAccount(IsAuthenticatedWithBlocked):
    def has_permission(self, request, view):
        is_authenticated = super().has_permission(request, view)
        if not is_authenticated:
            return False
        return request.user.user_type == UserTypes.CUSTOMER_COMPANY


class IsCustomerManagerAccount(IsAuthenticatedWithBlocked):
    def has_permission(self, request, view):
        is_authenticated = super().has_permission(request, view)
        if not is_authenticated:
            return False
        return request.user.user_type == UserTypes.CUSTOMER_MANAGER
