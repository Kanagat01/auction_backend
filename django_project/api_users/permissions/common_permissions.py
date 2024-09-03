from datetime import datetime
from rest_framework.permissions import BasePermission


class IsActiveUser(BasePermission):
    """
    Allows access only to active users.
    """

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False

        user = request.user
        if hasattr(user, 'customer_company'):
            subscription = user.customer_company.subscription
        elif hasattr(user, 'customer_manager'):
            subscription = user.customer_manager.company.subscription
        elif hasattr(user, 'transporter_company'):
            subscription = user.transporter_company.subscription
            if user.transporter_company.balance <= 0:
                return False
        elif hasattr(user, 'transporter_manager'):
            subscription = user.transporter_manager.company.subscription
            if user.transporter_manager.company.balance <= 0:
                return False
        else:
            return False

        today = datetime.now()
        return user.subscription_paid or today.day <= subscription.days_without_payment
