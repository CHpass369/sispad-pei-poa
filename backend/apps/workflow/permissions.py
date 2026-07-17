from rest_framework.permissions import BasePermission


class WorkflowPermission(BasePermission):
    """Permission for workflow module."""

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
        return True


class RevisionPermission(BasePermission):
    """Permission for revisiones. Only assigned reviewers can modify."""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return True
        return request.user.is_superuser or request.user.roles.filter(
            nombre__in=['superadmin', 'tecnico_admin', 'planificador', 'tecnico_operativo']
        ).exists()

    def has_object_permission(self, request, view, obj):
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return True
        if request.user.is_superuser:
            return True
        if request.user.roles.filter(nombre='superadmin').exists():
            return True
        if hasattr(obj, 'revisor') and obj.revisor_id == request.user.pk:
            return True
        return False


class AprobacionPermission(BasePermission):
    """Permission for aprobaciones. Only superadmin and admins can approve."""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return True
        return request.user.is_superuser or request.user.roles.filter(
            nombre__in=['superadmin', 'tecnico_admin', 'planificador', 'jefe_ue']
        ).exists()

    def has_object_permission(self, request, view, obj):
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return True
        if request.user.is_superuser:
            return True
        return request.user.roles.filter(
            nombre__in=['superadmin', 'tecnico_admin', 'planificador']
        ).exists()
