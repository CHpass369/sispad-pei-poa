from rest_framework.permissions import BasePermission


class POAUPermission(BasePermission):
    """Permission for POAU module. Operador and jefe_ue roles required for unit-level writes."""

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
        if obj.estado in ('aprobado', 'enviado'):
            return request.user.roles.filter(nombre='superadmin').exists()
        from apps.organizacion.models import AsignacionUsuarioUnidad
        return AsignacionUsuarioUnidad.objects.filter(
            usuario=request.user,
            unidad=obj.unidad,
            activo=True,
        ).exists()


class POAUActividadPermission(BasePermission):
    """Permission for POAU activities."""

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
        if obj.poau.estado in ('aprobado', 'enviado'):
            return request.user.is_superuser or request.user.roles.filter(
                nombre='superadmin'
            ).exists()
        return True
