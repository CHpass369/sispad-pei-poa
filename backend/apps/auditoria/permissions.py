from rest_framework.permissions import BasePermission


class AuditoriaPermission(BasePermission):
    """Permission for auditoria module. Read-only for all, write for superadmin only."""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return True
        return request.user.is_superuser or request.user.roles.filter(
            nombre='superadmin'
        ).exists()

    def has_object_permission(self, request, view, obj):
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return True
        return request.user.is_superuser or request.user.roles.filter(
            nombre='superadmin'
        ).exists()
