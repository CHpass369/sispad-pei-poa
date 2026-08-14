"""Lote L1 — clasificadores presupuestarios 2026.

Lee ``catalogo.clasificador_item`` (gestión 2026, baseline MEFP) y puebla:
FuenteFinanciamiento (21), OrganismoFinanciador (160), ObjetoGasto (505,
jerárquico 5 niveles), ClasificadorInstitucional (568), RubroRecurso (350) y
FinalidadFuncion (145). Las versiones 2026 vigentes sembradas (RM 249) se
reutilizan por (tipo, gestion); nunca se marca vigente una versión nueva.
"""
from apps.catalogos.importer.base import (
    ReporteLote,
    vigencia_desde,
    leer_items_clasificador,
    orden_bfs,
    profundidad,
    reconciliar_item_origen,
    upsert,
    version_clasificador,
    zfill_codigo,
)
from apps.catalogos.models import (
    ClasificadorInstitucional,
    FinalidadFuncion,
    FuenteFinanciamiento,
    ObjetoGasto,
    OrganismoFinanciador,
    RubroRecurso,
    VersionClasificador,
)

# En los clasificadores versionados solo se actualizan campos no
# semánticos: la asociación (codigo, gestion, version, padre) es inmutable.
CAMPOS_ACTUALIZABLES = {'denominacion', 'descripcion', 'metadatos_importacion'}

# Nivel del ObjetoGasto por profundidad: el catálogo trae 5 niveles y el
# modelo declara 4 choices (grupo/subgrupo/partida/detalle); el 5.º se
# asigna a 'detalle' conservando la profundidad en metadatos.
NIVEL_OBJETO_GASTO_POR_PROFUNDIDAD = {
    1: ObjetoGasto.NIVEL_GRUPO,
    2: ObjetoGasto.NIVEL_SUBGRUPO,
    3: ObjetoGasto.NIVEL_PARTIDA,
    4: ObjetoGasto.NIVEL_DETALLE,
    5: ObjetoGasto.NIVEL_DETALLE,
}


def _metadatos(clasificador, fila, gestion, extra=None):
    metadatos = {
        'fuente': 'catalogo_maestro',
        'esquema': 'catalogo',
        'tabla': 'clasificador_item',
        'clasificador': clasificador,
        'gestion_origen': gestion,
        'item_uuid': str(fila['item_uuid']),
        'estado_homologacion': fila.get('estado_homologacion'),
        'archivo_origen': fila.get('archivo_origen'),
    }
    if extra:
        metadatos.update(extra)
    return metadatos


def importar_fuentes(reporte, gestion):
    filas = leer_items_clasificador('FUENTE_FINANCIAMIENTO', gestion)
    if not filas:
        return
    version = version_clasificador(
        VersionClasificador.TIPO_FUENTE_FINANCIAMIENTO, gestion,
        'Importado del catálogo maestro — pendiente de homologación',
    )
    reporte.fuente = f'FUENTE_FINANCIAMIENTO ({len(filas)})'
    for fila in filas:
        codigo = zfill_codigo(fila['codigo'], 2)
        upsert(
            FuenteFinanciamiento,
            claves={'codigo': codigo, 'gestion': gestion},
            valores={
                'denominacion': fila['denominacion'],
                'descripcion': fila['descripcion'] or '',
                'version_clasificador': version,
                'fuente_normativa': '',
                'fecha_vigencia_desde': vigencia_desde(gestion),
                'metadatos_importacion': _metadatos(
                    'FUENTE_FINANCIAMIENTO', fila, gestion,
                ),
            },
            reporte=reporte,
            campos_actualizables=CAMPOS_ACTUALIZABLES,
        )
    reporte.conteos_modelo['FuenteFinanciamiento'] = (
        FuenteFinanciamiento.objects.filter(gestion=gestion).count()
    )


def importar_organismos(reporte, gestion):
    filas = leer_items_clasificador('ORGANISMO_FINANCIADOR', gestion)
    if not filas:
        return
    version = version_clasificador(
        VersionClasificador.TIPO_ORGANISMO_FINANCIADOR, gestion,
        'Importado del catálogo maestro — pendiente de homologación',
    )
    reporte.fuente = f'ORGANISMO_FINANCIADOR ({len(filas)})'
    for fila in filas:
        codigo = zfill_codigo(fila['codigo'], 3)
        upsert(
            OrganismoFinanciador,
            claves={'codigo': codigo, 'gestion': gestion},
            valores={
                'denominacion': fila['denominacion'],
                'descripcion': fila['descripcion'] or '',
                'version_clasificador': version,
                'fuente_normativa': '',
                'fecha_vigencia_desde': vigencia_desde(gestion),
                'metadatos_importacion': _metadatos(
                    'ORGANISMO_FINANCIADOR', fila, gestion,
                ),
            },
            reporte=reporte,
            campos_actualizables=CAMPOS_ACTUALIZABLES,
        )
    reporte.conteos_modelo['OrganismoFinanciador'] = (
        OrganismoFinanciador.objects.filter(gestion=gestion).count()
    )


def importar_objetos_gasto(reporte, gestion):
    filas = orden_bfs(leer_items_clasificador('OBJETO_GASTO', gestion))
    if not filas:
        return
    version = version_clasificador(
        VersionClasificador.TIPO_OBJETO_GASTO, gestion,
        'Importado del catálogo maestro — pendiente de homologación',
    )
    reporte.fuente = f'OBJETO_GASTO ({len(filas)})'
    por_uuid = {fila['item_uuid']: fila for fila in filas}
    objeto_por_item = {}
    for fila in filas:
        codigo = zfill_codigo(fila['codigo'], 5)
        profundidad_item = profundidad(fila, por_uuid)
        padre = objeto_por_item.get(fila.get('parent_uuid'))
        obj = upsert(
            ObjetoGasto,
            claves={'codigo': codigo, 'gestion': gestion},
            valores={
                'denominacion': fila['denominacion'],
                'descripcion': fila['descripcion'] or '',
                'version_clasificador': version,
                'padre': padre,
                'nivel': NIVEL_OBJETO_GASTO_POR_PROFUNDIDAD.get(
                    profundidad_item, ObjetoGasto.NIVEL_DETALLE,
                ),
                'fuente_normativa': '',
                'fecha_vigencia_desde': vigencia_desde(gestion),
                'metadatos_importacion': _metadatos(
                    'OBJETO_GASTO', fila, gestion,
                    {'profundidad': profundidad_item},
                ),
            },
            reporte=reporte,
            campos_actualizables=CAMPOS_ACTUALIZABLES,
        )
        objeto_por_item[fila['item_uuid']] = obj
        if padre is None and fila.get('parent_uuid') is not None:
            reporte.warnings.append(
                f'OBJETO_GASTO {codigo}: parent_uuid sin resolver en el lote.'
            )
    reporte.conteos_modelo['ObjetoGasto'] = (
        ObjetoGasto.objects.filter(gestion=gestion).count()
    )


def importar_institucional(reporte, gestion):
    filas = leer_items_clasificador('INSTITUCIONAL', gestion)
    reporte.fuente = f'INSTITUCIONAL ({len(filas)})'
    for fila in filas:
        upsert(
            ClasificadorInstitucional,
            claves={'codigo': fila['codigo'], 'gestion': gestion},
            valores={
                'denominacion': fila['denominacion'],
                'descripcion': fila['descripcion'] or '',
                'fuente_normativa': '',
                'fecha_vigencia_desde': vigencia_desde(gestion),
                'metadatos_importacion': _metadatos(
                    'INSTITUCIONAL', fila, gestion,
                    {
                        'sigla': fila.get('sigla') or '',
                        'es_entidad_principal': fila['codigo'] == '1312',
                        'entidad_principal': '1312',
                    },
                ),
            },
            reporte=reporte,
        )
    reporte.conteos_modelo['ClasificadorInstitucional'] = (
        ClasificadorInstitucional.objects.filter(gestion=gestion).count()
    )


def importar_rubros(reporte, gestion):
    filas = orden_bfs(leer_items_clasificador('RUBRO_RECURSO', gestion))
    reporte.fuente = f'RUBRO_RECURSO ({len(filas)})'
    por_uuid = {fila['item_uuid']: fila for fila in filas}
    for fila in filas:
        upsert(
            RubroRecurso,
            claves={'codigo': fila['codigo'], 'gestion': gestion},
            valores={
                'denominacion': fila['denominacion'],
                'descripcion': fila['descripcion'] or '',
                'fuente_normativa': '',
                'fecha_vigencia_desde': vigencia_desde(gestion),
                'metadatos_importacion': _metadatos(
                    'RUBRO_RECURSO', fila, gestion,
                    {'profundidad': profundidad(fila, por_uuid)},
                ),
            },
            reporte=reporte,
        )
    reporte.conteos_modelo['RubroRecurso'] = (
        RubroRecurso.objects.filter(gestion=gestion).count()
    )


def importar_finalidades(reporte, gestion):
    filas = orden_bfs(leer_items_clasificador('FINALIDAD_FUNCION', gestion))
    reporte.fuente = f'FINALIDAD_FUNCION ({len(filas)})'
    por_uuid = {fila['item_uuid']: fila for fila in filas}
    for fila in filas:
        upsert(
            FinalidadFuncion,
            claves={'codigo': fila['codigo'], 'gestion': gestion},
            valores={
                'denominacion': fila['denominacion'],
                'descripcion': fila['descripcion'] or '',
                'fuente_normativa': '',
                'fecha_vigencia_desde': vigencia_desde(gestion),
                'metadatos_importacion': _metadatos(
                    'FINALIDAD_FUNCION', fila, gestion,
                    {'profundidad': profundidad(fila, por_uuid)},
                ),
            },
            reporte=reporte,
        )
    reporte.conteos_modelo['FinalidadFuncion'] = (
        FinalidadFuncion.objects.filter(gestion=gestion).count()
    )


def importar(reporte, gestion):
    """Punto de entrada del lote L1 (clasificadores)."""
    reconciliar_item_origen(reporte)
    importar_fuentes(reporte, gestion)
    importar_organismos(reporte, gestion)
    importar_objetos_gasto(reporte, gestion)
    importar_institucional(reporte, gestion)
    importar_rubros(reporte, gestion)
    importar_finalidades(reporte, gestion)
    return reporte
