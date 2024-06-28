from rest_framework.permissions import IsAuthenticated


class IsPaidAccount(IsAuthenticated):
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

        return request.user.groups.filter(name='special_group').exists()
