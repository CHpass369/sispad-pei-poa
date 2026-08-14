"""Lote L2 — marco superior PGDESA/PDESA y acuerdos.

Lee ``core.instrumento`` (9) y ``sispe.elemento`` y puebla:
- ``planificacion.InstrumentoPlanificacion`` (reutilizado, H1) + TipoInstrumento.
- ``codificacion.EjePGDESA`` (7), ``ComponentePDESA`` (38, eje por 1.er
  segmento del código, H5) y ``LineamientoPAD`` (170, correlativo LL 001..170,
  H6) con la relación CONTIENE (170) en ``LineamientoPAD.componente``.

Los catálogos de codificación se versionan por ``VersionCatalogoPlan``:
se reutiliza o crea un Plan del tipo del instrumento con la gestión de
inicio como versión de trabajo (borrador, nunca vigente).
"""
from datetime import date

from apps.catalogos.importer.base import (
    ReporteLote,
    acotar,
    leer_filas,
    upsert,
)
from apps.codificacion.models import (
    ComponentePDESA,
    EjePGDESA,
    EntidadTerritorialCGEO,
    LineamientoPAD,
    VersionCatalogoPlan,
)
from apps.planificacion.models import Plan
from apps.planificacion.models_v2 import (
    EstadosInstrumento,
    InstrumentoPlanificacion,
    TipoInstrumento,
)

# Estado del instrumento del catálogo → estado del kernel V2.
ESTADO_INSTRUMENTO = {
    'OFICIAL': EstadosInstrumento.APROBADO,
    'OFICIAL_PUBLICADO': EstadosInstrumento.APROBADO,
    'FORMULACION': EstadosInstrumento.EN_FORMULACION,
    'FUENTE_PRIMARIA': EstadosInstrumento.EN_FORMULACION,
    'HISTORICO': EstadosInstrumento.BORRADOR,
    'PENDIENTE_MAESTROS_OFICIALES': EstadosInstrumento.BORRADOR,
}

NIVEL_INSTRUMENTO = {
    'NACIONAL': 'nacional',
    'SECTORIAL': 'sectorial',
    'GLOBAL': 'nacional',
}

# Entidad territorial CGEO de los lineamientos PAD del municipio (GAM
# Sacaba); si no existe, se toma la primera entidad disponible.
ENTIDAD_TERRITORIAL_CODIGO = '031001'

SQL_INSTRUMENTOS = """
SELECT instrumento_uuid, codigo, tipo, nombre, nivel, gestion_inicio,
       gestion_fin, estado
FROM core.instrumento ORDER BY codigo
"""

SQL_ELEMENTOS_POR_TIPO = """
SELECT e.elemento_uuid, e.codigo_oficial, e.codigo_sistema, e.denominacion
FROM sispe.elemento e
JOIN core.instrumento i ON i.instrumento_uuid = e.instrumento_uuid
WHERE i.tipo = %s {filtro_extra}
ORDER BY e.codigo_sistema
"""


def _tipo_instrumento(fila):
    codigo = fila['tipo']
    tipo, _ = TipoInstrumento.objects.get_or_create(
        codigo=codigo,
        defaults={
            'nombre': f'Instrumento {codigo}',
            'nivel': NIVEL_INSTRUMENTO.get(fila.get('nivel'), 'nacional'),
            'horizonte_anios': (
                fila['gestion_fin'] - fila['gestion_inicio'] + 1
                if fila.get('gestion_inicio') and fila.get('gestion_fin')
                else None
            ),
            'entidad_emisora': 'Órgano rector nacional',
            'activo': True,
        },
    )
    return tipo


def importar_instrumentos(reporte):
    filas = leer_filas(SQL_INSTRUMENTOS)
    reporte.fuente = f'core.instrumento ({len(filas)})'
    for fila in filas:
        tipo = _tipo_instrumento(fila)
        periodo_inicio = fila.get('gestion_inicio') or fila.get('gestion_fin')
        estado = ESTADO_INSTRUMENTO.get(fila.get('estado'), EstadosInstrumento.BORRADOR)
        upsert(
            InstrumentoPlanificacion,
            claves={'codigo': fila['codigo']},
            valores={
                'tipo': tipo,
                'nombre': fila['nombre'],
                'periodo_inicio': periodo_inicio,
                'periodo_fin': fila.get('gestion_fin'),
                'ambito': NIVEL_INSTRUMENTO.get(fila.get('nivel'), 'nacional'),
                'descripcion': (
                    f'Importado de core.instrumento (estado origen '
                    f'{fila.get("estado") or "sin estado"}).'
                ),
                'estado': estado,
            },
            reporte=reporte,
            campos_actualizables={
                'nombre', 'periodo_inicio', 'periodo_fin', 'estado', 'ambito',
            },
        )
    reporte.conteos_modelo['InstrumentoPlanificacion'] = (
        InstrumentoPlanificacion.objects.count()
    )
    return {fila['codigo']: fila for fila in filas}


def _plan_para(instrumento, tipo_plan):
    """Reutiliza el Plan del tipo solicitado o lo crea para el instrumento."""
    plan = Plan.objects.filter(tipo=tipo_plan, codigo=instrumento['codigo']).first()
    if plan is not None:
        return plan
    gestion_inicio = instrumento.get('gestion_inicio') or instrumento.get('gestion_fin')
    gestion_fin = instrumento.get('gestion_fin') or gestion_inicio
    return Plan.objects.create(
        codigo=instrumento['codigo'],
        nombre=instrumento['nombre'],
        tipo=tipo_plan,
        gestion_inicio=gestion_inicio,
        gestion_fin=gestion_fin,
        fecha_vigencia_desde=date(gestion_inicio, 1, 1),
        activo=True,
        descripcion=(
            'Creado por el importador del catálogo maestro '
            f'(instrumento {instrumento["codigo"]}).'
        ),
    )


def _version_catalogo(plan, gestion):
    version, _ = VersionCatalogoPlan.objects.get_or_create(
        plan=plan,
        gestion=gestion,
        defaults={
            'estado': VersionCatalogoPlan.ESTADO_BORRADOR,
            'norma_aprobacion': '',
            'clasificacion_fuente': VersionCatalogoPlan.FUENTE_REFERENCIAL,
            'procedencia_fuente': (
                'Importado del catálogo maestro (importar_catalogo_maestro).'
            ),
        },
    )
    return version


def _segmentos(codigo_oficial):
    """Segmentos del código punteado (``1.1`` → ['1', '1'])."""
    return str(codigo_oficial or '').split('.')


def _segmento_codigo(fila):
    """Código de 2 dígitos del eje desde codigo_oficial o codigo_sistema."""
    codigo_oficial = fila.get('codigo_oficial')
    if codigo_oficial is not None and str(codigo_oficial).strip():
        return str(codigo_oficial).zfill(2)
    sufijo = str(fila.get('codigo_sistema') or '').split('.')[-1]
    return sufijo[-2:].zfill(2) if sufijo else ''


def importar_ejes(reporte, instrumento):
    filas = leer_filas(
        SQL_ELEMENTOS_POR_TIPO.format(filtro_extra='AND e.tipo_elemento = %s'),
        ['PGDESA', 'EJE'],
    )
    reporte.fuente = f'PGDESA EJE ({len(filas)})'
    plan = _plan_para(instrumento, 'pgdesa')
    gestion = instrumento.get('gestion_inicio') or instrumento.get('gestion_fin')
    version = _version_catalogo(plan, gestion)

    ejes = {}
    for fila in filas:
        codigo = _segmento_codigo(fila)
        obj = upsert(
            EjePGDESA,
            claves={'codigo': codigo, 'version_catalogo': version},
            valores={
                'denominacion': acotar(fila['denominacion'], 500),
                'activo': True,
            },
            reporte=reporte,
            campos_actualizables={'denominacion'},
        )
        ejes[codigo] = obj
    reporte.conteos_modelo['EjePGDESA'] = (
        EjePGDESA.objects.filter(version_catalogo=version).count()
    )
    return version, ejes


def importar_componentes(reporte, instrumento, version_ejes, ejes):
    filas = leer_filas(
        SQL_ELEMENTOS_POR_TIPO.format(filtro_extra='AND e.tipo_elemento = %s'),
        ['PDESA', 'COMPONENTE'],
    )
    reporte.fuente = f'PDESA COMPONENTE ({len(filas)})'
    plan = _plan_para(instrumento, 'pdesa')
    gestion = instrumento.get('gestion_inicio') or instrumento.get('gestion_fin')
    version = _version_catalogo(plan, gestion)

    componentes = {}
    for fila in filas:
        segmentos = _segmentos(fila['codigo_oficial'])
        eje_codigo = segmentos[0].zfill(2)
        codigo = segmentos[1].zfill(2)
        eje = ejes.get(eje_codigo) or EjePGDESA.objects.filter(
            codigo=eje_codigo, version_catalogo=version_ejes,
        ).first()
        if eje is None:
            reporte.warnings.append(
                f'PDESA COMPONENTE {fila["codigo_sistema"]}: '
                f'eje {eje_codigo} no encontrado (H5 por segmento).'
            )
            continue
        obj = upsert(
            ComponentePDESA,
            claves={
                'eje': eje,
                'codigo': codigo,
                'version_catalogo': version,
            },
            valores={
                'denominacion': acotar(fila['denominacion'], 500),
                'activo': True,
            },
            reporte=reporte,
            campos_actualizables={'denominacion'},
        )
        componentes[(eje_codigo, codigo)] = obj
    reporte.conteos_modelo['ComponentePDESA'] = (
        ComponentePDESA.objects.filter(version_catalogo=version).count()
    )
    return version, componentes


def importar_lineamientos(reporte, instrumento, version_pdesa, componentes):
    filas = leer_filas(
        SQL_ELEMENTOS_POR_TIPO.format(filtro_extra='AND e.tipo_elemento = %s'),
        ['PDESA', 'LINEAMIENTO'],
    )
    reporte.fuente = f'PDESA LINEAMIENTO ({len(filas)})'
    entidad = (
        EntidadTerritorialCGEO.objects.filter(
            codigo=ENTIDAD_TERRITORIAL_CODIGO,
        ).first()
        or EntidadTerritorialCGEO.objects.first()
    )
    if entidad is None:
        raise RuntimeError(
            'No existe EntidadTerritorialCGEO para vincular los LineamientoPAD.'
        )

    lineamiento_por_sistema = {}
    for correlativo, fila in enumerate(filas, start=1):
        codigo = str(correlativo).zfill(3)
        obj = upsert(
            LineamientoPAD,
            claves={
                'entidad_territorial': entidad,
                'codigo': codigo,
                'version_catalogo': version_pdesa,
            },
            valores={
                'denominacion': acotar(fila['denominacion'], 500),
                'activo': True,
            },
            reporte=reporte,
            campos_actualizables={'denominacion'},
        )
        lineamiento_por_sistema[fila['codigo_sistema']] = obj
    reporte.conteos_modelo['LineamientoPAD'] = (
        LineamientoPAD.objects.filter(version_catalogo=version_pdesa).count()
    )
    return entidad, lineamiento_por_sistema


def importar_con_tiene(reporte, version_pdesa, componentes, lineamiento_por_sistema):
    """Relación CONTIENE (170): componente del lineamiento (opción A)."""
    filas = leer_filas(
        """
        SELECT o.codigo_oficial AS componente_codigo,
               d.codigo_sistema AS lineamiento_sistema
        FROM sispe.relacion_elemento r
        JOIN sispe.elemento o ON o.elemento_uuid = r.origen_uuid
        JOIN sispe.elemento d ON d.elemento_uuid = r.destino_uuid
        WHERE r.tipo_relacion = 'CONTIENE'
          AND o.tipo_elemento = 'COMPONENTE'
          AND d.tipo_elemento = 'LINEAMIENTO'
        ORDER BY d.codigo_sistema
        """
    )
    reporte.fuente = f'CONTIENE COMPONENTE→LINEAMIENTO ({len(filas)})'
    vinculados = 0
    for fila in filas:
        segmentos = _segmentos(fila['componente_codigo'])
        if len(segmentos) < 2:
            continue
        componente = componentes.get((segmentos[0].zfill(2), segmentos[1].zfill(2)))
        lineamiento = lineamiento_por_sistema.get(fila['lineamiento_sistema'])
        if componente is None or lineamiento is None:
            continue
        if lineamiento.componente_id != componente.pk:
            lineamiento.componente = componente
            lineamiento.save(update_fields=['componente', 'updated_at'])
        vinculados += 1
    if vinculados < len(filas):
        reporte.warnings.append(
            f'CONTIENE: {len(filas) - vinculados} de {len(filas)} vínculos '
            'no resueltos.'
        )
    return vinculados


def importar(reporte, gestion=None):
    """Punto de entrada del lote L2 (marco superior).

    ``gestion`` se acepta por firma uniforme pero no se usa: la versión de
    catálogo de los ejes/componentes/lineamientos es la gestión de inicio
    del instrumento (PGDESA 2026 / PDESA 2026).
    """
    instrumentos = importar_instrumentos(reporte)

    instrumento_pgdesa = instrumentos.get('PGDESA-2026-2035')
    instrumento_pdesa = instrumentos.get('PDESA-2026-2030')
    if instrumento_pgdesa is None or instrumento_pdesa is None:
        raise RuntimeError(
            'No se encontraron los instrumentos PGDESA-2026-2035 / '
            'PDESA-2026-2030 en core.instrumento.'
        )

    version_ejes, ejes = importar_ejes(reporte, instrumento_pgdesa)
    version_pdesa, componentes = importar_componentes(
        reporte, instrumento_pdesa, version_ejes, ejes,
    )
    entidad, lineamientos = importar_lineamientos(
        reporte, instrumento_pdesa, version_pdesa, componentes,
    )
    importar_con_tiene(
        reporte, version_pdesa, componentes, lineamientos,
    )
    return reporte
