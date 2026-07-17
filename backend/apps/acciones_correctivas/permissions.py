from rest_framework.permissions import BasePermission


class AccionesCorrectivasPermission(BasePermission):
    """Permission for acciones correctivas module."""

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
        if hasattr(obj, 'responsible') and obj.responsible_id == request.user.pk:
            return True
        if obj.status in ('cumplida', 'cerrada', 'cancelada'):
            return False
        from apps.organizacion.models import AsignacionUsuarioUnidad
        if hasattr(obj, 'responsible_unit') and obj.responsible_unit_id:
            return AsignacionUsuarioUnidad.objects.filter(
                usuario=request.user,
                unidad=obj.responsible_unit,
                activo=True,
            ).exists()
        return False


class CompromisoAccionCorrectivaPermission(BasePermission):
    """Permission for compromisos de acciones correctivas."""

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
        if obj.status == 'cumplido':
            return False
        return True
