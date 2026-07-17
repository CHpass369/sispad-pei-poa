from rest_framework.permissions import BasePermission


class SeguimientoPermission(BasePermission):
    """Permission for seguimiento module."""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return True
        return request.user.is_superuser or request.user.roles.filter(
            nombre__in=['superadmin', 'tecnico_admin', 'planificador', 'operador', 'jefe_ue']
        ).exists()

    def has_object_permission(self, request, view, obj):
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return True
        if request.user.is_superuser:
            return True
        if request.user.roles.filter(nombre__in=['superadmin', 'tecnico_admin']).exists():
            return True
        if hasattr(obj, 'unidad_organizacional'):
            from apps.organizacion.models import AsignacionUsuarioUnidad
            return AsignacionUsuarioUnidad.objects.filter(
                usuario=request.user,
                unidad=obj.unidad_organizacional,
                activo=True,
            ).exists()
        return True


class AlertaPermission(BasePermission):
    """Permission for alertas."""

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
        if obj.activa:
            return request.user.is_superuser or request.user.roles.filter(
                nombre__in=['superadmin', 'tecnico_admin', 'planificador']
            ).exists()
        return False


class UmbralConfiguracionPermission(BasePermission):
    """Permission for umbrales de configuracion. Admin only."""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return True
        return request.user.is_superuser or request.user.roles.filter(
            nombre__in=['superadmin', 'tecnico_admin']
        ).exists()

    def has_object_permission(self, request, view, obj):
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return True
        return request.user.is_superuser or request.user.roles.filter(
            nombre__in=['superadmin', 'tecnico_admin']
        ).exists()
