from api_users.models import UserTypes
from rest_framework.permissions import IsAuthenticated


class IsCustomerCompanyAccount(IsAuthenticated):
    def has_permission(self, request, view):
        is_authenticated = super().has_permission(request, view)
        if not is_authenticated:
            return False
        return request.user.user_type == UserTypes.CUSTOMER_COMPANY


class IsCustomerManagerAccount(IsAuthenticated):
    def has_permission(self, request, view):
        is_authenticated = super().has_permission(request, view)
        if not is_authenticated:
            return False
        return request.user.user_type == UserTypes.CUSTOMER_MANAGER
