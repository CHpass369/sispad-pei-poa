from rest_framework.permissions import BasePermission


class DocumentosPermission(BasePermission):
    """Permission for documentos module."""

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
        if hasattr(obj, 'subido_por') and obj.subido_por_id == request.user.pk:
            return True
        return request.user.roles.filter(
            nombre__in=['superadmin', 'tecnico_admin']
        ).exists()
