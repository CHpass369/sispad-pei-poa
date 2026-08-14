"""Lote L3 — acuerdos internacionales.

- ODS (17) → ``articulacion.AcuerdoInternacional`` (upsert, ya poblado).
- NDC (35) / NDT (17) / KMGBF (23) → ``articulacion.MetaAcuerdoInternacional``
  con código = ``codigo_sistema`` del catálogo (p. ej. NDC3.AGROPECUARIO.M01).
"""
from apps.catalogos.importer.base import ReporteLote, leer_filas, upsert
from apps.articulacion.models import AcuerdoInternacional, MetaAcuerdoInternacional

SQL_ODS = """
SELECT e.elemento_uuid, e.codigo_oficial, e.codigo_sistema, e.denominacion
FROM sispe.elemento e
JOIN core.instrumento i ON i.instrumento_uuid = e.instrumento_uuid
WHERE i.tipo = 'ODS'
ORDER BY e.codigo_sistema
"""

SQL_METAS = """
SELECT i.tipo AS tipo, i.codigo AS instrumento, e.elemento_uuid,
       e.codigo_sistema, e.denominacion
FROM sispe.elemento e
JOIN core.instrumento i ON i.instrumento_uuid = e.instrumento_uuid
WHERE i.tipo IN ('NDC', 'NDT', 'KMGBF')
ORDER BY i.tipo, e.codigo_sistema
"""


def importar_ods(reporte):
    filas = leer_filas(SQL_ODS)
    reporte.fuente = f'ODS ({len(filas)})'
    for fila in filas:
        codigo = str(fila['codigo_oficial']).zfill(2)
        upsert(
            AcuerdoInternacional,
            claves={'tipo_acuerdo': 'ODS', 'codigo': codigo},
            valores={
                'denominacion': fila['denominacion'],
                'rango_valido': '',
                'es_codigo_oficial': True,
                'activo': True,
            },
            reporte=reporte,
            campos_actualizables={'denominacion'},
        )
    reporte.conteos_modelo['AcuerdoInternacional.ODS'] = (
        AcuerdoInternacional.objects.filter(tipo_acuerdo='ODS').count()
    )


def importar_metas(reporte):
    filas = leer_filas(SQL_METAS)
    reporte.fuente = f'NDC/NDT/KMGBF ({len(filas)})'
    for fila in filas:
        upsert(
            MetaAcuerdoInternacional,
            claves={
                'tipo_acuerdo': fila['tipo'],
                'codigo': fila['codigo_sistema'],
            },
            valores={
                'denominacion': fila['denominacion'],
                'instrumento_origen': fila['instrumento'],
                'activo': True,
                'metadatos_importacion': {
                    'fuente': 'catalogo_maestro',
                    'esquema': 'sispe',
                    'tabla': 'elemento',
                    'item_uuid': str(fila['elemento_uuid']),
                },
            },
            reporte=reporte,
            campos_actualizables={'denominacion'},
        )
    for tipo in ('NDC', 'NDT', 'KMGBF'):
        reporte.conteos_modelo[f'MetaAcuerdoInternacional.{tipo}'] = (
            MetaAcuerdoInternacional.objects.filter(
                tipo_acuerdo=tipo,
            ).count()
        )


def importar(reporte, gestion=None):
    """Punto de entrada del lote L3 (acuerdos)."""
    importar_ods(reporte)
    importar_metas(reporte)
    return reporte
