from rest_framework.permissions import BasePermission


class EvaluacionPermission(BasePermission):
    """Permission for evaluacion module. Evaluador role required."""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return True
        return request.user.is_superuser or request.user.roles.filter(
            nombre__in=['superadmin', 'tecnico_admin', 'evaluador']
        ).exists()

    def has_object_permission(self, request, view, obj):
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return True
        if request.user.is_superuser:
            return True
        if obj.status in ('completada', 'aprobada'):
            return request.user.is_superuser or request.user.roles.filter(
                nombre__in=['superadmin', 'tecnico_admin']
            ).exists()
        return request.user.roles.filter(
            nombre__in=['superadmin', 'tecnico_admin', 'evaluador']
        ).exists()


class CriterioEvaluacionPermission(BasePermission):
    """Permission for criterios de evaluacion."""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return True
        return request.user.is_superuser or request.user.roles.filter(
            nombre__in=['superadmin', 'tecnico_admin', 'evaluador']
        ).exists()

    def has_object_permission(self, request, view, obj):
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return True
        return True


class RecomendacionPermission(BasePermission):
    """Permission for recomendaciones."""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return True
        return request.user.is_superuser or request.user.roles.filter(
            nombre__in=['superadmin', 'tecnico_admin', 'evaluador']
        ).exists()

    def has_object_permission(self, request, view, obj):
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return True
        if obj.status == 'cumplida':
            return False
        return True
