"""Alcance organizacional para la cadena POAU de `articulacion` (ADR-003).

`AccionPOA`, `OperacionPOAU` y `ActividadPOAU` alimentan las pantallas POAU
(Físico y Recursos). Tenían control de capacidad (`ArticulacionPermisos`) pero
NINGÚN filtro territorial: un usuario acotado a su unidad listaba —y podía
abrir— las acciones de toda la alcaldía.

`ScopePOAUUnidadMixin` acota el queryset a las UO efectivas del usuario y
rechaza escribir sobre una unidad ajena. Cada viewset declara la ruta que lleva
de su modelo a la unidad responsable:

    AccionPOA      → unidad_responsable_id
    OperacionPOAU  → accion_poa__unidad_responsable_id
    ActividadPOAU  → operacion__accion_poa__unidad_responsable_id

Un alcance GLOBAL (SUPER_ADMIN, jefaturas) no se ve afectado: el filtro solo
muerde a quien tiene alcance acotado. Sin alcances vigentes el queryset queda
vacío, nunca abierto (fail-closed, igual que `ScopeResolver`).
"""
from rest_framework.exceptions import PermissionDenied

from apps.accounts.services_scope import GLOBAL_SCOPE, ScopeResolver
from apps.gestion.mixins import gestion_del_candado


class ScopePOAUUnidadMixin:
    """Acota por unidad responsable. Definir `scope_unidad_lookup`."""

    #: Ruta ORM del modelo hasta la UO responsable.
    scope_unidad_lookup = 'unidad_responsable_id'
    #: Ruta desde la instancia hasta la UO, para validar escrituras.
    scope_unidad_attrs = ('unidad_responsable_id',)

    def _unidades_en_alcance(self):
        """IDs de UO donde puede operar, o None si el alcance es total."""
        request = self.request
        if request.user.is_superuser:
            return None
        unidades = ScopeResolver.unidades_efectivas(
            request.user, gestion_del_candado(request).id,
        )
        return None if GLOBAL_SCOPE in unidades else unidades

    def get_queryset(self):
        queryset = super().get_queryset()
        unidades = self._unidades_en_alcance()
        if unidades is None:
            return queryset
        if not unidades:
            return queryset.none()
        return queryset.filter(**{f'{self.scope_unidad_lookup}__in': unidades})

    def _autorizar_unidad(self, unidad_id):
        unidades = self._unidades_en_alcance()
        if unidades is None:
            return
        if unidad_id is None or unidad_id not in unidades:
            raise PermissionDenied('Unidad organizacional fuera de su alcance.')

    def _unidad_objetivo(self, serializer):
        """UO a la que apunta lo que se está por guardar."""
        raise NotImplementedError

    def perform_create(self, serializer):
        self._autorizar_unidad(self._unidad_objetivo(serializer))
        serializer.save()

    def perform_update(self, serializer):
        self._autorizar_unidad(self._unidad_objetivo(serializer))
        serializer.save()


class ScopeAccionPOAMixin(ScopePOAUUnidadMixin):
    scope_unidad_lookup = 'unidad_responsable_id'

    def _unidad_objetivo(self, serializer):
        unidad = serializer.validated_data.get(
            'unidad_responsable',
            getattr(serializer.instance, 'unidad_responsable', None),
        )
        return getattr(unidad, 'pk', None)


class ScopeOperacionPOAUMixin(ScopePOAUUnidadMixin):
    scope_unidad_lookup = 'accion_poa__unidad_responsable_id'

    def _unidad_objetivo(self, serializer):
        accion = serializer.validated_data.get(
            'accion_poa', getattr(serializer.instance, 'accion_poa', None),
        )
        return getattr(accion, 'unidad_responsable_id', None)


class ScopeActividadPOAUMixin(ScopePOAUUnidadMixin):
    scope_unidad_lookup = 'operacion__accion_poa__unidad_responsable_id'

    def _unidad_objetivo(self, serializer):
        operacion = serializer.validated_data.get(
            'operacion', getattr(serializer.instance, 'operacion', None),
        )
        accion = getattr(operacion, 'accion_poa', None)
        return getattr(accion, 'unidad_responsable_id', None)
