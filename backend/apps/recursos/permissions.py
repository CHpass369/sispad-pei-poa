from rest_framework.permissions import BasePermission


class RecursosPermission(BasePermission):
    """Permission for recursos module (estimaciones de recursos)."""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return True
        return request.user.is_superuser or request.user.roles.filter(
            nombre__in=['superadmin', 'tecnico_admin', 'planificador', 'operador']
        ).exists()

    def has_object_permission(self, request, view, obj):
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return True
        return request.user.is_superuser or request.user.roles.filter(
            nombre__in=['superadmin', 'tecnico_admin', 'planificador']
        ).exists()
