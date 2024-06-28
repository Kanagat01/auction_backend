from api_users.models import UserModel, UserTypes
from api_users.models.subscriptions import CustomerSubscriptions
from api_users.permissions.common_permissions import IsAuthenticatedWithBlocked


class IsCustomerCompanyAccount(IsAuthenticatedWithBlocked):
    def has_permission(self, request, view):
        is_authenticated = super().has_permission(request, view)
        if not is_authenticated:
            return False
        return request.user.user_type == UserTypes.CUSTOMER_COMPANY


class IsPaidCustomerAccount(IsAuthenticatedWithBlocked):
    """
    Custom permission that inherits from IsAuthenticated and
    adds additional restrictions (replace with your logic).
    """

    def has_permission(self, request, view):
        # Check that the user is authenticated
        is_authenticated = super().has_permission(request, view)

        if not is_authenticated:
            return False

        # Additional checks for your custom logic
        # Example: Check if the user belongs to a specific group
        user: UserModel = request.user
        if user.user_type == UserTypes.CUSTOMER_COMPANY:
            return user.customer_profile.subscription == CustomerSubscriptions.PAID
        return False


class IsCustomerManagerAccount(IsAuthenticatedWithBlocked):
    def has_permission(self, request, view):
        is_authenticated = super().has_permission(request, view)
        if not is_authenticated:
            return False
        return request.user.user_type == UserTypes.CUSTOMER_MANAGER
