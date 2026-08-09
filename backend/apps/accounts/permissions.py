"""Autorización por capacidades (ADR-003).

El backend es la autoridad de permisos: cada endpoint declara las capacidades
que requiere. El frontend solo consulta `/api/v2/me/capabilities`.
"""
from rest_framework import permissions


def listar_capacidades(usuario):
    """Códigos de capacidad efectivos del usuario (superusuario: todas)."""
    if not usuario or not usuario.is_authenticated:
        return []
    if usuario.is_superuser:
        from apps.accounts.models import Capacidad
        return list(
            Capacidad.objects.filter(activo=True)
            .values_list('codigo', flat=True)
        )
    return list(
        usuario.roles
        .filter(activo=True, capacidades__activo=True)
        .values_list('capacidades__codigo', flat=True)
        .distinct()
        .order_by('capacidades__codigo')
    )


def tiene_capacidad(usuario, codigo_capacidad):
    if not usuario or not usuario.is_authenticated:
        return False
    if usuario.is_superuser:
        return True
    return usuario.roles.filter(
        activo=True,
        capacidades__codigo=codigo_capacidad,
        capacidades__activo=True,
    ).exists()


class TieneCapacidad(permissions.BasePermission):
    """Permiso DRF parametrizable: `TieneCapacidad('sis_pe.pad.edit')`."""

    def __init__(self, codigo_capacidad):
        self.codigo_capacidad = codigo_capacidad

    def has_permission(self, request, view):
        return tiene_capacidad(request.user, self.codigo_capacidad)

    def has_object_permission(self, request, view, obj):
        return self.has_permission(request, view)


class TieneAlgunaCapacidad(permissions.BasePermission):
    """Permiso DRF: el usuario debe tener al menos una de las capacidades."""

    def __init__(self, *codigos_capacidad):
        self.codigos_capacidad = codigos_capacidad

    def has_permission(self, request, view):
        return any(
            tiene_capacidad(request.user, codigo)
            for codigo in self.codigos_capacidad
        )

    def has_object_permission(self, request, view, obj):
        return self.has_permission(request, view)
