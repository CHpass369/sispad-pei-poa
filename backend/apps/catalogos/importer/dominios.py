"""Lote L6 — dominios y validaciones.

- ``catalogo.dominio_item`` (53): UnidadMedida (13), TipoOperacion (2),
  TipoProducto (6) como CatalogoBase por (codigo, gestion); el resto de los
  dominios (TIPO_INDICADOR, TIPO_REQUERIMIENTO, ESTADO_FLUJO, SISPE.*) queda
  documentado en metadatos (choices de los modelos destino, T posterior).
- ``catalogo.validacion`` (9) → ``catalogos.ValidacionPlataforma`` (nuevo).
"""
from apps.catalogos.importer.base import (
    ReporteLote, leer_filas, resolver_gestion, upsert, vigencia_desde,
)
from apps.catalogos.models import (
    TipoOperacion,
    TipoProducto,
    UnidadMedida,
    ValidacionPlataforma,
)

SQL_DOMINIOS = """
SELECT dominio_uuid, dominio, codigo, denominacion, descripcion, grupo,
       simbolo
FROM catalogo.dominio_item
ORDER BY dominio, codigo
"""

SQL_VALIDACIONES = """
SELECT validacion_uuid, codigo, modulo, control, regla, nivel, efecto
FROM catalogo.validacion
ORDER BY codigo
"""

# dominios del catálogo que aterrizan en CatalogoBase por (codigo, gestion).
MODELOS_DOMINIO = {
    'POA.UNIDAD_MEDIDA': UnidadMedida,
    'POA.TIPO_OPERACION': TipoOperacion,
    'POA.TIPO_PRODUCTO': TipoProducto,
}

DOMINIOS_DOCUMENTADOS = {
    'POA.TIPO_INDICADOR': 'choices de TipoIndicador (articulación)',
    'POA.TIPO_REQUERIMIENTO': 'choices de TipoRequerimiento (articulación)',
    'POA.ESTADO_FLUJO': 'choices de EstadoFlujo (flujos POA)',
    'SISPE.estado_oficialidad': 'choices de estado de oficialidad SISPE',
    'SISPE.tipo_articulacion': 'choices de tipo de articulación SISPE',
}


def importar_dominios(reporte, gestion):
    filas = leer_filas(SQL_DOMINIOS)
    reporte.fuente = f'catalogo.dominio_item ({len(filas)})'
    por_dominio = {}
    for fila in filas:
        por_dominio.setdefault(fila['dominio'], []).append(fila)

    gestion_fiscal = resolver_gestion(gestion)
    for dominio, modelo in MODELOS_DOMINIO.items():
        for fila in por_dominio.get(dominio, []):
            upsert(
                modelo,
                claves={'codigo': fila['codigo'], 'gestion': gestion_fiscal},
                valores={
                    'denominacion': fila['denominacion'],
                    'descripcion': fila['descripcion'] or '',
                    'fuente_normativa': '',
                    'fecha_vigencia_desde': vigencia_desde(gestion),
                    'metadatos_importacion': {
                        'fuente': 'catalogo_maestro',
                        'esquema': 'catalogo',
                        'tabla': 'dominio_item',
                        'dominio': dominio,
                        'dominio_uuid': str(fila['dominio_uuid']),
                        'simbolo': fila.get('simbolo') or '',
                        'grupo': fila.get('grupo') or '',
                    },
                },
                reporte=reporte,
            )
        reporte.conteos_modelo[modelo.__name__] = (
            modelo.objects.filter(gestion__anio=gestion).count()
        )

    for dominio, descripcion in DOMINIOS_DOCUMENTADOS.items():
        if dominio in por_dominio:
            reporte.warnings.append(
                f'Dominio {dominio} ({len(por_dominio[dominio])} ítems) no '
                f'importado: se parametriza como {descripcion}.'
            )


def importar_validaciones(reporte):
    filas = leer_filas(SQL_VALIDACIONES)
    reporte.fuente = f'catalogo.validacion ({len(filas)})'
    for fila in filas:
        upsert(
            ValidacionPlataforma,
            claves={'codigo': fila['codigo']},
            valores={
                'modulo': fila['modulo'] or '',
                'control': fila['control'] or '',
                'regla': fila['regla'] or '',
                'nivel': fila['nivel'] or 'ERROR',
                'efecto': fila['efecto'] or 'BLOQUEA_ENVIO',
                'activo': True,
                'metadatos_importacion': {
                    'fuente': 'catalogo_maestro',
                    'esquema': 'catalogo',
                    'tabla': 'validacion',
                    'validacion_uuid': str(fila['validacion_uuid']),
                },
            },
            reporte=reporte,
            campos_actualizables={
                'modulo', 'control', 'regla', 'nivel', 'efecto', 'activo',
            },
        )
    reporte.conteos_modelo['ValidacionPlataforma'] = (
        ValidacionPlataforma.objects.count()
    )


def importar(reporte, gestion):
    """Punto de entrada del lote L6 (dominios/validaciones)."""
    importar_dominios(reporte, gestion)
    importar_validaciones(reporte)
    return reporte
