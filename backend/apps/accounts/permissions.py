from rest_framework.permissions import BasePermission


class AccountsPermission(BasePermission):
    """Permission for accounts module. Users can view, superadmin manages."""

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
        if request.user.is_superuser:
            return True
        if request.user.roles.filter(nombre='superadmin').exists():
            return True
        return obj.pk == request.user.pk


class IsOwnProfileOrAdmin(BasePermission):
    """Allow users to manage their own profile, admins can manage all."""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return True
        return True

    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser:
            return True
        if request.user.roles.filter(nombre='superadmin').exists():
            return True
        return obj.pk == request.user.pk
