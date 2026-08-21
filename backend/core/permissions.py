"""Custom DRF permissions for the core app."""

from rest_framework.permissions import BasePermission

from core.models import UserProfile


class IsOrganizationAdmin(BasePermission):
    """Allows access only to Organization Admins (or superusers/staff)."""

    def has_permission(self, request, view):
        user = request.user
        if not (user and user.is_authenticated):
            return False
        if user.is_superuser or user.is_staff:
            return True
        profile = getattr(user, "profile", None)
        return bool(profile and profile.role == UserProfile.Role.ADMIN)
