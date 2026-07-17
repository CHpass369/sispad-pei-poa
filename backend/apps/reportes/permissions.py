from rest_framework.permissions import BasePermission


class ReportesPermission(BasePermission):
    """Permission for reportes module."""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return True
        return request.user.is_superuser or request.user.roles.filter(
            nombre__in=['superadmin', 'tecnico_admin', 'planificador']
        ).exists()

    def has_object_permission(self, request, view, obj):
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return True
        if request.user.is_superuser:
            return True
        if hasattr(obj, 'generado_por') and obj.generado_por_id == request.user.pk:
            return True
        return request.user.roles.filter(
            nombre__in=['superadmin', 'tecnico_admin']
        ).exists()
