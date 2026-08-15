"""Paginación DUAL: modo página (DRF estándar) + modo cursor opcional.

Por qué existe (Fase C del plan de optimización Postgres, P2 data-pagination):

- El frontend Angular (audit.component.ts, imports.component.ts) consume el
  contrato PageNumberPagination de DRF: `{count, results, next, previous}`,
  y navega construyendo `?page=N` a mano, sin usar los enlaces
  `next/previous` de la respuesta.
- La auditoría es una tabla append-only que crece sin límite y las
  importaciones también acumulan filas: el modo cursor (posicional, sin
  OFFSET profundo) prepara el terreno para ese crecimiento.
- `PaginacionDualPagination` mantiene el comportamiento actual por defecto
  (mismo contrato, `?page=N` igual que hoy → frontend intacto). Solo si el
  cliente envía `?cursor=` se delega a `CursorPagination`, devolviendo el
  MISMO contrato `{count, results, next, previous}`, con `next/previous`
  como URLs de cursor completas. Así un cliente nuevo puede optar por
  cursor sin romper a los existentes.

El orden del cursor es fijo por subclase (CursorPagination exige un campo
estable y no soporta `__` en el ordering):
- `AuditoriaCursorPagination` → `-creado_en` (auditoría, append-only).
- `ImportacionCursorPagination` → `-created_at` (importaciones).
"""
from django.core.exceptions import ImproperlyConfigured
from rest_framework.pagination import CursorPagination, PageNumberPagination
from rest_framework.response import Response


class CursorConCountPagination(CursorPagination):
    """CursorPagination que mantiene el contrato DRF del frontend.

    DRF no cuenta por defecto en modo cursor (`self.page` es una lista sin
    `paginator`). Aquí se captura el COUNT del queryset filtrado antes del
    corte posicional: una sola consulta `COUNT(*)` por request, la misma que
    hace PageNumberPagination vía `paginator.count`.
    """

    cursor_query_param = 'cursor'
    page_size = 25

    def paginate_queryset(self, queryset, request, view=None):
        self.count = queryset.count()
        return super().paginate_queryset(queryset, request, view)

    def get_paginated_response(self, data):
        return Response({
            'count': self.count,
            'results': data,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
        })


class AuditoriaCursorPagination(CursorConCountPagination):
    """Cursor por `-creado_en` para la auditoría (tabla append-only)."""
    ordering = '-creado_en'


class ImportacionCursorPagination(CursorConCountPagination):
    """Cursor por `-created_at` para las importaciones de planillas."""
    ordering = '-created_at'


class PaginacionDualPagination(PageNumberPagination):
    """PageNumberPagination por defecto; `?cursor=` activa el modo cursor.

    El frontend actual navega con `?page=N` y nunca envía `cursor`, así que
    su comportamiento es idéntico al de hoy. Los clientes futuros (tablas
    grandes) envían `?cursor=` — vacío para la primera página, o el valor de
    `next/previous` de la respuesta anterior — y reciben el mismo contrato
    `{count, results, next, previous}`, con `next/previous` como URLs de
    cursor completas.
    """

    page_size = 25
    cursor_query_param = 'cursor'
    cursor_pagination_class = None

    def paginate_queryset(self, queryset, request, view=None):
        if self.cursor_query_param in request.query_params:
            if self.cursor_pagination_class is None:
                raise ImproperlyConfigured(
                    'PaginacionDualPagination requiere `cursor_pagination_class` '
                    'para operar en modo cursor.'
                )
            self._cursor_paginador = self.cursor_pagination_class()
            return self._cursor_paginador.paginate_queryset(
                queryset, request, view,
            )
        self._cursor_paginador = None
        return super().paginate_queryset(queryset, request, view)

    def get_paginated_response(self, data):
        paginador = getattr(self, '_cursor_paginador', None)
        if paginador is not None:
            return paginador.get_paginated_response(data)
        return super().get_paginated_response(data)


class AuditoriaDualPagination(PaginacionDualPagination):
    """Paginación dual para listados de auditoría (cursor por `-creado_en`)."""
    cursor_pagination_class = AuditoriaCursorPagination


class ImportacionDualPagination(PaginacionDualPagination):
    """Paginación dual para importaciones (cursor por `-created_at`)."""
    cursor_pagination_class = ImportacionCursorPagination
