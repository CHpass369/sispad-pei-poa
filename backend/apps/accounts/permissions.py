"""Autorización por capacidades (ADR-003).

El backend es la autoridad de permisos: cada endpoint declara las capacidades
que requiere. El frontend solo consulta `/api/v2/me/capabilities`.
"""
import uuid

from rest_framework import permissions

from apps.accounts.services_scope import ScopeResolver


def listar_capacidades(usuario, roles=None):
    """Códigos de capacidad efectivos del usuario (superusuario: todas)."""
    from apps.accounts.models import Capacidad

    if not usuario or not usuario.is_authenticated:
        return []
    if usuario.is_superuser and roles is None:
        return list(
            Capacidad.objects.filter(activo=True)
            .values_list('codigo', flat=True)
        )
    roles = usuario.roles.all() if roles is None else roles
    role_ids = [rol.pk for rol in roles]
    return list(
        Capacidad.objects.filter(
            roles__pk__in=role_ids, roles__activo=True, activo=True,
        )
        .values_list('codigo', flat=True)
        .distinct()
        .order_by('codigo')
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


# --- F2a: capacidad + scope organizacional -------------------------------

# Sentinel: el parámetro de gestión venía en la request pero no es un UUID
# válido. Se distingue de None (ausente → sin filtro) para fallar cerrado.
GESTION_INVALIDA = object()


def resolver_gestion_id(request, view=None, param='gestion_id'):
    kwargs = getattr(view, 'kwargs', None) or {}
    valor = kwargs.get(param)
    if valor is None:
        query = getattr(request, 'query_params', None)
        if query is None:
            query = getattr(request, 'GET', {})
        valor = query.get(param)
    if valor is None:
        return None
    try:
        return uuid.UUID(str(valor))
    except (ValueError, AttributeError, TypeError):
        return GESTION_INVALIDA


def resolve_unidad_id(obj):
    """UO de un objeto del dominio por convención (F2a), por duck typing.

    Sin imports de apps de negocio: CORE no depende de SIS-POA. Orden de
    lookup:

    1. `unidad_id` directo no nulo (AccionCortoPlazo, Operacion, ...).
    2. Ascenso por la jerarquía `actividad → operacion → accion`
       (Tarea, Actividad, Operacion con unidad nula).
    3. None si no se pudo resolver.

    El guard contra ciclos usa ids de objeto en memoria.
    """
    nodo = obj
    visitados = set()
    while nodo is not None and id(nodo) not in visitados:
        visitados.add(id(nodo))
        unidad_id = getattr(nodo, 'unidad_id', None)
        if unidad_id is not None:
            return unidad_id
        nodo = (
            getattr(nodo, 'actividad', None)
            or getattr(nodo, 'operacion', None)
            or getattr(nodo, 'accion', None)
            or getattr(nodo, 'poau', None)
        )
    return None


def _unidades_de_objeto(obj):
    """Set de `unidad_id` asociadas al objeto (convención F2a).

    - Objetos tipo PoA (exponen related manager `acciones`): todas las UO de
      sus acciones; las acciones sin UO no restringen. Un PoA sin acciones
      devuelve set vacío → no hay nada que restringir a nivel de objeto.
    - Resto: la UO resuelta por `_resolve_unidad_id`, o set vacío si el
      objeto no expone UO.
    """
    acciones = getattr(obj, 'acciones', None)
    if acciones is not None and hasattr(acciones, 'values_list'):
        return set(acciones.values_list('unidad_id', flat=True)) - {None}
    unidad_id = resolve_unidad_id(obj)
    return {unidad_id} if unidad_id is not None else set()


class CapacidadConScope(permissions.BasePermission):
    """Permiso DRF: capacidad + alcance organizacional (F2a / ADR-003).

    Uso: `CapacidadConScope('sis_poa.poau.edit', gestion_id_param='gestion_id')`.
    `gestion_id_param` es el nombre del kwarg de URL o query param que trae
    el id de la gestión fiscal; si está presente, los alcances se filtran
    por esa gestión.
    """

    def __init__(
        self, codigo_capacidad, gestion_id_param=None, allow_empty_list=False,
    ):
        self.codigo_capacidad = codigo_capacidad
        self.gestion_id_param = gestion_id_param
        self.allow_empty_list = allow_empty_list

    def _gestion_id(self, request, view):
        """UUID de gestión de la request, None si ausente, sentinel si inválido."""
        if not self.gestion_id_param:
            return None
        return resolver_gestion_id(request, view, self.gestion_id_param)

    def _bypass_superuser(self, request):
        """Bypass para superusuarios Django (decisión F2b pre).

        Permite que el admin Django actual pueda operar sin necesidad de
        tener un AlcanceOrganizacional sembrado explícitamente.
        """
        user = getattr(request, 'user', None)
        return bool(user and user.is_authenticated and user.is_superuser)

    def has_permission(self, request, view):
        if self._bypass_superuser(request):
            return True
        # 1-2. Autenticado + capacidad (tiene_capacidad valida ambos).
        if not tiene_capacidad(request.user, self.codigo_capacidad):
            return False
        # 3. Filtro opcional por gestión (kwarg de URL o query param).
        gestion_id = self._gestion_id(request, view)
        if gestion_id is GESTION_INVALIDA:
            return False
        # list/create: no hay objeto aún; basta con que exista alguna UO
        # efectiva (set vacío = no puede operar en ninguna).
        unidades = ScopeResolver.unidades_efectivas(request.user, gestion_id)
        if unidades:
            return True
        return self.allow_empty_list and getattr(view, 'action', None) in (
            'list', 'por_unidad',
        )

    def has_object_permission(self, request, view, obj):
        if self._bypass_superuser(request):
            return True
        if not tiene_capacidad(request.user, self.codigo_capacidad):
            return False
        gestion_id = self._gestion_id(request, view)
        if gestion_id is GESTION_INVALIDA:
            return False
        unidades = _unidades_de_objeto(obj)
        if not unidades:
            # Objeto sin UO resoluble (p. ej. PoA sin acciones): nada que
            # restringir a nivel de objeto (convención F2a).
            return True
        return all(
            ScopeResolver.puede_operar(request.user, uid, gestion_id)
            for uid in unidades
        )
