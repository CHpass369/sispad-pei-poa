"""Lote L7b — sector económico presupuestario.

``catalogo.clasificador_item`` SECTOR_ECONOMICO (406, 3 niveles) →
``catalogos.SectorEconomicoPresupuestario`` (nuevo, R5): código punteado
(``1.1.1``), padre FK resuelto por parent_uuid en orden BFS y nivel derivado
de la profundidad. Independiente de ``codificacion.SectorEconomico`` (SS PAD).
"""
from apps.catalogos.importer.base import (
    ReporteLote,
    leer_items_clasificador,
    orden_bfs,
    profundidad,
    resolver_gestion,
    upsert,
    vigencia_desde,
)
from apps.catalogos.models import SectorEconomicoPresupuestario


def importar(reporte, gestion):
    """Punto de entrada del lote L7b (sector)."""
    filas = orden_bfs(leer_items_clasificador('SECTOR_ECONOMICO', gestion))
    reporte.fuente = f'SECTOR_ECONOMICO ({len(filas)})'
    por_uuid = {fila['item_uuid']: fila for fila in filas}
    sector_por_item = {}
    gestion_fiscal = resolver_gestion(gestion)
    for fila in filas:
        padre = sector_por_item.get(fila.get('parent_uuid'))
        profundidad_item = profundidad(fila, por_uuid)
        obj = upsert(
            SectorEconomicoPresupuestario,
            claves={'codigo': fila['codigo'], 'gestion': gestion_fiscal},
            valores={
                'denominacion': fila['denominacion'] or f'Sector {fila["codigo"]}',
                'descripcion': fila['descripcion'] or '',
                'padre': padre,
                'nivel': str(profundidad_item),
                'fuente_normativa': '',
                'fecha_vigencia_desde': vigencia_desde(gestion),
                'metadatos_importacion': {
                    'fuente': 'catalogo_maestro',
                    'esquema': 'catalogo',
                    'tabla': 'clasificador_item',
                    'clasificador': 'SECTOR_ECONOMICO',
                    'gestion_origen': gestion,
                    'item_uuid': str(fila['item_uuid']),
                    'profundidad': profundidad_item,
                    'es_raiz': padre is None,
                },
            },
            reporte=reporte,
            campos_actualizables={'denominacion', 'descripcion'},
        )
        sector_por_item[fila['item_uuid']] = obj
    reporte.conteos_modelo['SectorEconomicoPresupuestario'] = (
        SectorEconomicoPresupuestario.objects.filter(gestion__anio=gestion).count()
    )
    return reporte
