"""Lote L4 — estructura programática y recursos 2027 (sispoa).

- ``sispoa.catalogo_programa`` (34) → ``presupuesto.ProgramaPresupuestario``
  (codigo = codigo_inicio; los rangos se colapsan al inicio).
- ``sispoa.catalogo_actividad_especifica`` (15) → ``ProyectoPresupuestario``
  + ``ActividadPresupuestaria``; los programas referenciados que no existen
  (p. ej. 319 dentro del rango 310-319) se crean sintéticos (H9).
- ``sispoa.catalogo_recurso`` (15) → ``techos.TechoPresupuestario`` 2027
  (1:1 con GestionFiscal, si no existe) + ``RecursoTecho`` monto=0 (R16).
"""
from decimal import Decimal

from apps.catalogos.importer.base import (
    ReporteLote,
    acotar,
    leer_filas,
    upsert,
    zfill_codigo,
)
from apps.catalogos.models import FuenteFinanciamiento, OrganismoFinanciador
from apps.gestion.models import GestionFiscal
from apps.presupuesto.models import (
    ActividadPresupuestaria,
    ProgramaPresupuestario,
    ProyectoPresupuestario,
)
from apps.techos.models import RecursoTecho, TechoPresupuestario

# Los datos de sispoa (programa/actividad/recurso) son gestión 2027
# (H9): se importan con esta gestión fija, independiente de --gestion.
GESTION_SISPOA = 2027


SQL_PROGRAMAS = """
SELECT programa_uuid, codigo_inicio, codigo_fin, denominacion_programa,
       finalidad_funcion, sector_economico, tipo_registro, gestion
FROM sispoa.catalogo_programa
WHERE gestion = %s
ORDER BY codigo_inicio
"""

SQL_ACTIVIDADES = """
SELECT actividad_uuid, programa, proyecto, actividad, denominacion,
       finalidad_funcion, sector_economico, gestion
FROM sispoa.catalogo_actividad_especifica
WHERE gestion = %s
ORDER BY programa, actividad
"""

SQL_RECURSOS = """
SELECT recurso_uuid, codigo_regla, tipo_recurso, rubro,
       fuente_financiamiento, organismo_financiador, entidad_otorgante,
       denominacion_otorgante, gestion
FROM sispoa.catalogo_recurso
ORDER BY codigo_regla
"""


def importar_programas(reporte, gestion):
    filas = leer_filas(SQL_PROGRAMAS, [gestion])
    reporte.fuente = f'sispoa.catalogo_programa ({len(filas)})'
    codigos = set()
    for fila in filas:
        codigo = zfill_codigo(fila['codigo_inicio'], 3)
        codigos.add(codigo)
        detalle = f'Rango {fila["codigo_inicio"]}-{fila["codigo_fin"]}'
        if fila.get('finalidad_funcion'):
            detalle += f' | Finalidad {fila["finalidad_funcion"]}'
        if fila.get('sector_economico'):
            detalle += f' | Sector {fila["sector_economico"]}'
        upsert(
            ProgramaPresupuestario,
            claves={'codigo': codigo, 'gestion': gestion},
            valores={
                'nombre': fila['denominacion_programa'],
                'descripcion': f'{detalle} ({fila["tipo_registro"] or "RANGO"})',
                'activo': True,
            },
            reporte=reporte,
            campos_actualizables={'nombre', 'descripcion', 'activo'},
        )
    reporte.conteos_modelo['ProgramaPresupuestario'] = (
        ProgramaPresupuestario.objects.filter(gestion=gestion).count()
    )
    return codigos


def _programa_sintetico(reporte, codigo, gestion):
    """Crea un programa sintético para un código referenciado sin programa.

    Busca el rango del catálogo que lo contiene (H9: 319 dentro de 310-319)
    y reutiliza su denominación marcando la naturaleza sintética.
    """
    fila_rango = leer_filas(
        'SELECT codigo_inicio, codigo_fin, denominacion_programa '
        'FROM sispoa.catalogo_programa '
        'WHERE gestion = %s AND %s::int BETWEEN codigo_inicio::int '
        'AND codigo_fin::int ORDER BY codigo_inicio LIMIT 1',
        [gestion, codigo],
    )
    if fila_rango:
        nombre = f'{fila_rango[0]["denominacion_programa"]} (sintético)'
        descripcion = (
            f'Programa sintético creado por el importador: referenciado por '
            f'catalogo_actividad_especifica y contenido en el rango '
            f'{fila_rango[0]["codigo_inicio"]}-{fila_rango[0]["codigo_fin"]} '
            f'del catálogo.'
        )
    else:
        nombre = f'Programa sintético {codigo}'
        descripcion = (
            'Programa sintético creado por el importador: referenciado por '
            'catalogo_actividad_especifica y ausente de catalogo_programa.'
        )
    programa, _ = ProgramaPresupuestario.objects.get_or_create(
        codigo=codigo, gestion=gestion,
        defaults={'nombre': nombre, 'descripcion': descripcion, 'activo': True},
    )
    reporte.warnings.append(
        f'Programa sintético {codigo} creado para la actividad del catálogo '
        f'({nombre}).'
    )
    return programa


def importar_actividades(reporte, gestion, codigos_programa):
    filas = leer_filas(SQL_ACTIVIDADES, [gestion])
    reporte.fuente = f'sispoa.catalogo_actividad_especifica ({len(filas)})'
    for fila in filas:
        codigo_programa = zfill_codigo(fila['programa'], 3)
        programa = ProgramaPresupuestario.objects.filter(
            codigo=codigo_programa, gestion=gestion,
        ).first()
        if programa is None:
            programa = _programa_sintetico(reporte, codigo_programa, gestion)
            codigos_programa.add(codigo_programa)

        codigo_proyecto = zfill_codigo(fila['proyecto'], 3) or '000'
        proyecto, _ = ProyectoPresupuestario.objects.get_or_create(
            codigo=codigo_proyecto,
            programa=programa,
            gestion=gestion,
            defaults={
                'nombre': f'Proyecto {codigo_proyecto}',
                'activo': True,
            },
        )
        codigo_actividad = zfill_codigo(fila['actividad'], 3)
        upsert(
            ActividadPresupuestaria,
            claves={
                'codigo': codigo_actividad,
                'proyecto': proyecto,
                'gestion': gestion,
            },
            valores={
                'nombre': fila['denominacion'],
                'activo': True,
            },
            reporte=reporte,
            campos_actualizables={'nombre', 'activo'},
        )
    reporte.conteos_modelo['ProyectoPresupuestario'] = (
        ProyectoPresupuestario.objects.filter(gestion=gestion).count()
    )
    reporte.conteos_modelo['ActividadPresupuestaria'] = (
        ActividadPresupuestaria.objects.filter(gestion=gestion).count()
    )


def _resolver_fuente(codigo, gestion):
    """Resuelve un código único de fuente → FK; None si es variable/rango."""
    if codigo and str(codigo).strip().isdigit():
        return FuenteFinanciamiento.objects.filter(
            codigo=str(codigo).strip(), gestion=gestion,
        ).first()
    return None


def _resolver_organismo(codigo, gestion):
    if codigo and str(codigo).strip().isdigit():
        return OrganismoFinanciador.objects.filter(
            codigo=str(codigo).strip(), gestion=gestion,
        ).first()
    return None


def importar_recursos(reporte, gestion):
    filas = leer_filas(SQL_RECURSOS)
    reporte.fuente = f'sispoa.catalogo_recurso ({len(filas)})'

    gestion_fiscal = GestionFiscal.objects.filter(anio=gestion).first()
    if gestion_fiscal is None:
        gestion_fiscal = GestionFiscal.objects.create(
            anio=gestion,
            estado=GestionFiscal.Estado.PREPARACION,
            descripcion='Creada por el importador del catálogo maestro.',
            activa=True,
        )

    techo = TechoPresupuestario.objects.filter(
        gestion_fiscal=gestion_fiscal,
    ).first()
    if techo is None:
        fuente_base = (
            FuenteFinanciamiento.objects.filter(
                codigo='41', gestion=2026,
            ).first()
            or FuenteFinanciamiento.objects.filter(gestion=2026).first()
        )
        if fuente_base is None:
            raise RuntimeError(
                'No existe FuenteFinanciamiento 2026 para crear el techo 2027.'
            )
        techo = TechoPresupuestario.objects.create(
            gestion=gestion,
            gestion_fiscal=gestion_fiscal,
            monto_total=Decimal('0.00'),
            otras_afectaciones=Decimal('0.00'),
            fuente=fuente_base,
            organismo=None,
            concepto='Techo importado del catálogo maestro (sin montos, R16)',
            descripcion=(
                'Montos por flujo de techo; el catálogo maestro solo '
                'parametriza rubro/fuente/organismo/entidad otorgante.'
            ),
            activo=True,
        )
        reporte.creados += 1

    for orden, fila in enumerate(filas):
        fuente = _resolver_fuente(fila['fuente_financiamiento'], 2026)
        organismo = _resolver_organismo(
            fila['organismo_financiador'], 2026,
        )
        valores = {
            'techo': techo,
            'rubro': acotar(fila['rubro'] or '', 20),
            'rubro_descripcion': fila['tipo_recurso'] or '',
            'fuente': fuente or techo.fuente,
            'organismo': organismo,
            'entidad_otorgante': fila['denominacion_otorgante'] or '',
            'concepto': fila['codigo_regla'],
            'monto': Decimal('0.00'),
            'orden': orden,
        }
        recurso = RecursoTecho.objects.filter(
            techo=techo, concepto=fila['codigo_regla'],
        ).first()
        if recurso is None:
            RecursoTecho.objects.create(**valores)
            reporte.creados += 1
            continue
        cambios = {
            k: v for k, v in valores.items()
            if getattr(recurso, k) != v
        }
        if cambios:
            for k, v in cambios.items():
                setattr(recurso, k, v)
            recurso.save(update_fields=list(cambios))
            reporte.actualizados += 1
        else:
            reporte.omitidos += 1

    reporte.conteos_modelo['TechoPresupuestario'] = (
        TechoPresupuestario.objects.filter(gestion=gestion).count()
    )
    reporte.conteos_modelo['RecursoTecho'] = (
        RecursoTecho.objects.filter(techo=techo).count()
    )


def importar(reporte, gestion):
    """Punto de entrada del lote L4 (sispoa)."""
    codigos = importar_programas(reporte, gestion)
    importar_actividades(reporte, gestion, codigos)
    importar_recursos(reporte, gestion)
    return reporte
