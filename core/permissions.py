"""Explicit permission classes (no scattered `if user.is_staff`)."""
from rest_framework.permissions import SAFE_METHODS, BasePermission

from users.models import UserRole


class IsAdminRole(BasePermission):
    message = "Administrator access is required."

    def has_permission(self, request, view):
        u = request.user
        return bool(u and u.is_authenticated and u.is_active and (u.role == UserRole.ADMIN or u.is_superuser))


class HasDjangoPerm(BasePermission):
    """Use via subclass with `perm = "app.codename"`."""
    perm = None

    def has_permission(self, request, view):
        u = request.user
        return bool(u and u.is_authenticated and u.is_active and (u.is_superuser or (self.perm and u.has_perm(self.perm))))


class CanViewAuditLogs(HasDjangoPerm):
    perm = "audit.view_auditlog"
    message = "You do not have permission to view audit logs."


class IsOwner(BasePermission):
    """Object-level: object must belong to request.user via `owner_field` on the view (default `user`)."""
    message = "You do not have access to this resource."

    def has_object_permission(self, request, view, obj):
        field = getattr(view, "owner_field", "user")
        return getattr(obj, f"{field}_id", None) == request.user.id


class IsOwnerOrReadOnlyDemo(BasePermission):
    """Owner has full access; anyone authenticated may READ demo records."""
    message = "You do not have access to this resource."

    def has_object_permission(self, request, view, obj):
        if obj.user_id == request.user.id:
            return True
        return bool(request.method in SAFE_METHODS and getattr(obj, "is_demo_data", False))
IsAdminUser = IsAdminRole  # alias
