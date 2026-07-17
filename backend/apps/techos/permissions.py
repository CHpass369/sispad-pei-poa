from rest_framework.permissions import BasePermission


class TechosPermission(BasePermission):
    """Permission for techos presupuestarios."""

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
            nombre__in=['superadmin', 'tecnico_admin']
        ).exists()


class MovimientoTechoPermission(BasePermission):
    """Permission for movements on budget ceilings."""

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
        if obj.approved_by is not None:
            return False
        return request.user.is_superuser or request.user.roles.filter(
            nombre__in=['superadmin', 'tecnico_admin']
        ).exists()
