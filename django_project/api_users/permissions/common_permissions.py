from rest_framework.permissions import IsAuthenticated


class IsAuthenticatedWithBlocked(IsAuthenticated):
    def has_permission(self, request, view):
        is_authenticated = super().has_permission(request, view)
        if not is_authenticated:
            return False
        user = request.user
        return not user.blocked
