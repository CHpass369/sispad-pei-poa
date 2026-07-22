from rest_framework import permissions


class ArticulacionPermisos(permissions.BasePermission):
    """Permisos por acción: solo superadmin, planificador y técnico admin pueden modificar."""

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated
        return request.user.is_authenticated and (
            request.user.is_superuser
            or request.user.roles.filter(
                codigo__in=['superadmin', 'planificador', 'tecnico_admin']
            ).exists()
        )
