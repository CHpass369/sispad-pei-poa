"""Lote L5 — reglas GAM (catalogo.regla_gam, 21).

Mapea tipo_regla → ReglaPresupuestariaLegal.Tipo (ampliado), severidad
BLOQUEANTE/ADVERTENCIA y parametros {fuente, organismo, programa, actividad}
desde las columnas del catálogo. La gestión desde es 2027 (reglas 2027).
"""
from apps.catalogos.importer.base import ReporteLote, leer_filas, upsert
from apps.normativa.models import ReglaPresupuestariaLegal

SQL_REGLAS = """
SELECT regla_uuid, codigo_regla, tipo_regla, nombre, regla_resumen,
       condicion, fuente, organismo, programa, actividad, norma, severidad
FROM catalogo.regla_gam
ORDER BY codigo_regla
"""

# TODO(integracion-s2): el catálogo legacy tipa reglas con más variedad
# (PORCENTAJE/IMPUTACION/PROGRAMA/FUENTE/PERSONAL/DESTINO/CODIGO) que
# ReglaPresupuestariaLegal.Tipo en main. Mapeo conservador: LIMITE→limite,
# PORCENTAJE→minimo (análogo en main: gasto_sus/renta_dignidad usan minimo)
# y el resto a consistencia (fallback que el propio lote ya usa).
MAPEO_TIPO = {
    'LIMITE': ReglaPresupuestariaLegal.Tipo.LIMITE,
    'PORCENTAJE': ReglaPresupuestariaLegal.Tipo.MINIMO,
    'IMPUTACION': ReglaPresupuestariaLegal.Tipo.CONSISTENCIA,
    'PROGRAMA': ReglaPresupuestariaLegal.Tipo.CONSISTENCIA,
    'FUENTE': ReglaPresupuestariaLegal.Tipo.CONSISTENCIA,
    'PERSONAL': ReglaPresupuestariaLegal.Tipo.CONSISTENCIA,
    'DESTINO': ReglaPresupuestariaLegal.Tipo.CONSISTENCIA,
    'CODIGO': ReglaPresupuestariaLegal.Tipo.CONSISTENCIA,
}

MAPEO_SEVERIDAD = {
    'BLOQUEANTE': ReglaPresupuestariaLegal.Severidad.BLOQUEANTE,
    'ADVERTENCIA': ReglaPresupuestariaLegal.Severidad.ADVERTENCIA,
}

GESTION_DESDE = 2027


def importar(reporte, gestion):
    """Punto de entrada del lote L5 (reglas)."""
    filas = leer_filas(SQL_REGLAS)
    reporte.fuente = f'catalogo.regla_gam ({len(filas)})'
    for fila in filas:
        tipo = MAPEO_TIPO.get(fila['tipo_regla'])
        if tipo is None:
            reporte.warnings.append(
                f'Regla {fila["codigo_regla"]}: tipo_regla '
                f'"{fila["tipo_regla"]}" sin mapeo; se usa consistencia.'
            )
            tipo = ReglaPresupuestariaLegal.Tipo.CONSISTENCIA
        severidad = MAPEO_SEVERIDAD.get(
            fila['severidad'],
            ReglaPresupuestariaLegal.Severidad.BLOQUEANTE,
        )
        parametros = {
            clave: fila[clave]
            for clave in ('fuente', 'organismo', 'programa', 'actividad')
            if fila.get(clave)
        }
        descripcion = fila['regla_resumen'] or fila['condicion'] or fila['nombre']
        upsert(
            ReglaPresupuestariaLegal,
            claves={'codigo': fila['codigo_regla']},
            valores={
                'nombre': fila['nombre'],
                'descripcion': descripcion,
                'tipo': tipo,
                'severidad': severidad,
                'formula': fila['condicion'] or '',
                'parametros': parametros,
                'condicion_aplicabilidad': (
                    f'Importada del catálogo maestro (regla_gam '
                    f'{fila["codigo_regla"]}).'
                ),
                'gestion_desde': GESTION_DESDE,
                'gestion_hasta': None,
                'fuente_normativa': fila['norma'] or '',
                'mensaje': descripcion,
                'orden': 0,
                'activo': True,
            },
            reporte=reporte,
            campos_actualizables={
                'nombre', 'descripcion', 'tipo', 'severidad', 'formula',
                'parametros', 'fuente_normativa', 'mensaje',
            },
        )
    reporte.conteos_modelo['ReglaPresupuestariaLegal'] = (
        ReglaPresupuestariaLegal.objects.count()
    )
    return reporte
