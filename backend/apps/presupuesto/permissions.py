from rest_framework.permissions import BasePermission


class PresupuestoPermission(BasePermission):
    """Permission for presupuesto module."""

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


class LineaPresupuestariaPermission(BasePermission):
    """Permission for lineas presupuestarias."""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return True
        return request.user.is_superuser or request.user.roles.filter(
            nombre__in=['superadmin', 'tecnico_admin', 'operador', 'jefe_ue']
        ).exists()

    def has_object_permission(self, request, view, obj):
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return True
        if request.user.is_superuser:
            return True
        if request.user.roles.filter(nombre='superadmin').exists():
            return True
        if request.user.roles.filter(nombre__in=['operador', 'jefe_ue']).exists():
            from apps.organizacion.models import AsignacionUsuarioUnidad
            return AsignacionUsuarioUnidad.objects.filter(
                usuario=request.user,
                unidad__ues_asociadas=obj.ue,
                activo=True,
            ).exists()
        return False
