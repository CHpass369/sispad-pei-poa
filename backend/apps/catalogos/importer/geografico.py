"""Lote L7a — geográfico presupuestario MEFP.

``catalogo.clasificador_item`` GEOGRAFICO (603, 2026): códigos punteados
DD.PP.MM (``3.5.1`` Sacaba) → ``ClasificadorGeograficoPresupuestario``.
Raíces especiales planas (10 NACIONAL, 11 BINACIONAL, 20 BIDEPARTAMENTAL,
21 MULTIDEPARTAMENTAL) se mapean con provincia/municipio '0' (H7/R4).
El catálogo es intencionalmente independiente del CGEO INE (no se cruzan).
"""
from apps.catalogos.importer.base import (
    ReporteLote,
    leer_items_clasificador,
    orden_bfs,
    upsert,
    version_clasificador,
)
from apps.catalogos.models import (
    ClasificadorGeograficoPresupuestario,
    VersionClasificador,
)


def importar(reporte, gestion):
    """Punto de entrada del lote L7a (geográfico)."""
    filas = orden_bfs(leer_items_clasificador('GEOGRAFICO', gestion))
    if not filas:
        return
    version = version_clasificador(
        VersionClasificador.TIPO_GEOGRAFICO_PRESUPUESTARIO, gestion,
        'Importado del catálogo maestro — pendiente de homologación',
    )
    reporte.fuente = f'GEOGRAFICO ({len(filas)})'
    for fila in filas:
        partes = str(fila['codigo']).split('.')
        departamento = partes[0]
        provincia = partes[1] if len(partes) > 1 else '0'
        municipio = partes[2] if len(partes) > 2 else '0'
        upsert(
            ClasificadorGeograficoPresupuestario,
            claves={
                'version_clasificador': version,
                'departamento': departamento,
                'provincia': provincia,
                'municipio': municipio,
            },
            valores={
                'codigo_fuente': '|'.join(partes),
                'denominacion': fila['denominacion'],
                'procedencia_normativa': (
                    f'Importado del catálogo maestro (GEOGRAFICO {gestion}).'
                ),
            },
            reporte=reporte,
            campos_actualizables={'codigo_fuente', 'denominacion'},
        )
    reporte.conteos_modelo['ClasificadorGeograficoPresupuestario'] = (
        ClasificadorGeograficoPresupuestario.objects.filter(
            version_clasificador=version,
        ).count()
    )
    return reporte
