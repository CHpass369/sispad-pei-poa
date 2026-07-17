from rest_framework.permissions import BasePermission


class ModificacionesPermission(BasePermission):
    """Permission for modificaciones module."""

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
        if obj.estado in ('aprobada', 'cumplida'):
            return request.user.is_superuser or request.user.roles.filter(
                nombre__in=['superadmin', 'tecnico_admin']
            ).exists()
        if hasattr(obj, 'solicitado_por') and obj.solicitado_por_id == request.user.pk:
            return True
        return request.user.roles.filter(
            nombre__in=['superadmin', 'tecnico_admin', 'planificador']
        ).exists()


class SolicitudModificacionPermission(BasePermission):
    """Permission specifically for solicitud modifications."""

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
        if obj.estado == 'borrador':
            return obj.solicitado_por_id == request.user.pk or request.user.is_superuser
        if obj.estado == 'en_revision':
            return request.user.is_superuser or request.user.roles.filter(
                nombre__in=['superadmin', 'tecnico_admin', 'planificador']
            ).exists()
        return False
