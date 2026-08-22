"""Mixins de viewset que aplican el candado de SIS-POA (ADR-007).

Se aplican **viewset por viewset**, nunca de forma global: fuera de SIS-POA el
año no es una gestión fiscal operativa sino el horizonte de un plan (SIS-PE es
quinquenal 2026-2030) y el candado no corresponde. La excepción plurianual
está escrita en `docs/architecture/GESTION_FISCAL_AUDIT.md` §6.
"""
from rest_framework.exceptions import APIException

from . import candado


class GestionNoHabilitada(APIException):
    """409: se pidió operar fuera de la gestión habilitada.

    409 y no 400 porque no es un dato mal formado sino un conflicto con el
    estado del sistema, igual que `ERROR_409_INMUTABLE` en `apps/budget`. El
    `code` viaja en el cuerpo para que el frontend distinga este caso de
    cualquier otro conflicto.

    El `detail` va plano: `apps.core.exceptions.api_exception_handler` ya
    envuelve toda respuesta en `{'error': ...}`, y anidar acá otro `error`
    dejaba el cuerpo como `{'error': {'error': {...}}}`, donde el frontend no
    encontraba ni el mensaje ni el código.
    """

    status_code = 409

    def __init__(self, error):
        super().__init__({
            'detail': ' '.join(error.messages),
            'code': getattr(error, 'codigo', candado.CODIGO_FUERA_DE_GESTION),
        })


def gestion_del_candado(request):
    """La gestión habilitada para este request, o 409.

    Para los `viewsets.ViewSet` planos y las `APIView`, que no tienen
    `get_queryset` donde enganchar el mixin.
    """
    try:
        return candado.resolver_gestion(request)
    except candado.FueraDeGestionHabilitada as error:
        raise GestionNoHabilitada(error) from error


class GestionHabilitadaFilterMixin:
    """Acota el queryset a la gestión habilitada. Es la lectura del candado.

    Reemplaza al patrón `if gestion: qs.filter(...)` que estaba repetido por
    todos los viewsets: cuando el cliente no mandaba `?gestion=`, ese `if`
    devolvía **todas** las gestiones mezcladas. Acá no hay rama sin filtro.

    - `campo_gestion`: nombre del campo en el modelo (`gestion`, `gestion_fiscal`…).
    - `gestion_es_fk`: True si el campo es FK a `GestionFiscal` (la campaña
      PIP-DB-005/006/007 sigue abierta y conviven FK y año suelto).
    """

    campo_gestion = 'gestion'
    gestion_es_fk = False

    def get_queryset(self):
        gestion = gestion_del_candado(self.request)
        sufijo = '__anio' if self.gestion_es_fk else ''
        return super().get_queryset().filter(
            **{f'{self.campo_gestion}{sufijo}': gestion.anio},
        )


class CandadoGestionMixin:
    """Rechaza escrituras fuera de la gestión habilitada (409).

    Cubre el caso que el filtro de lectura no cubre: un `create` que trae
    `gestion` en el cuerpo apuntando a otro año.
    """

    campo_gestion = 'gestion'

    def _validar_candado(self, request):
        try:
            candado.validar_gestion(request.data.get(self.campo_gestion))
        except candado.FueraDeGestionHabilitada as error:
            raise GestionNoHabilitada(error) from error

    def create(self, request, *args, **kwargs):
        self._validar_candado(request)
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        self._validar_candado(request)
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        self._validar_candado(request)
        return super().partial_update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        self._validar_candado(request)
        return super().destroy(request, *args, **kwargs)


class CandadoSisPoaMixin(CandadoGestionMixin, GestionHabilitadaFilterMixin):
    """Candado duro completo: ni se lee ni se escribe fuera de la habilitada."""
