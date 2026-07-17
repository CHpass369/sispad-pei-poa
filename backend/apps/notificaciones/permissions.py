from rest_framework.permissions import BasePermission


class NotificacionesPermission(BasePermission):
    """Permission for notificaciones module. Users can manage their own notifications."""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return True
        return True

    def has_object_permission(self, request, view, obj):
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return True
        if request.user.is_superuser:
            return True
        if hasattr(obj, 'user') and obj.user_id == request.user.pk:
            return True
        if hasattr(obj, 'user') and obj.user_id != request.user.pk:
            return request.user.roles.filter(
                nombre__in=['superadmin', 'tecnico_admin']
            ).exists()
        return request.user.roles.filter(
            nombre__in=['superadmin', 'tecnico_admin']
        ).exists()


class TipoNotificacionPermission(BasePermission):
    """Permission for tipo notificacion (admin only for manage)."""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return True
        return request.user.is_superuser or request.user.roles.filter(
            nombre='superadmin'
        ).exists()

    def has_object_permission(self, request, view, obj):
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return True
        return request.user.is_superuser or request.user.roles.filter(
            nombre='superadmin'
        ).exists()
