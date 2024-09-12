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
            company = user.customer_company
            subscription = company.subscription
        elif hasattr(user, 'customer_manager'):
            company = user.customer_manager.company
            subscription = company.subscription
        elif hasattr(user, 'transporter_company'):
            company = user.transporter_company
            subscription = company.subscription
            if company.balance <= 0:
                return False
        elif hasattr(user, 'transporter_manager'):
            company  = user.transporter_manager.company
            subscription = company.subscription
            if company.balance <= 0:
                return False
        else:
            return True

        today = datetime.now()
        return company.subscription_paid or today.day <= subscription.days_without_payment
