"""Base del importador del catálogo maestro.

Provee el lector SQL calificado (esquemas ``core|catalogo|sispe|sispoa``),
el ordenamiento BFS de jerarquías, el upsert idempotente con conteo y el
reporte por lote. El modo dry-run se implementa en el comando envolviendo
cada lote en ``transaction.atomic()`` + ``set_rollback(True)``: la lectura,
transformación y conteo son idénticos a un commit, pero nada persiste.
"""
import json
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from datetime import date

from django.db import connection

from apps.catalogos.models import VersionClasificador
from apps.gestion.models import GestionFiscal


def resolver_gestion(gestion):
    """Resuelve un año a la instancia GestionFiscal de los modelos FK-izados.

    Los importadores (siembra ETL) crean la gestión si no existe, igual que el
    lote L0: nunca se inventa fuera de la siembra de catálogos (PIP-DB-003).
    """
    if isinstance(gestion, GestionFiscal):
        return gestion
    gestion_fiscal, _ = GestionFiscal.objects.get_or_create(
        anio=int(gestion),
        defaults={
            'estado': GestionFiscal.Estado.PREPARACION,
            'descripcion': 'Creada por el importador del catálogo maestro.',
            'activa': True,
        },
    )
    return gestion_fiscal


def vigencia_desde(gestion):
    """Fecha de vigencia inicial de un CatalogoBase (VigenciaModel)."""
    return date(gestion, 1, 1)


def acotar(texto, maximo):
    """Recorta un texto a ``maximo`` caracteres (denominaciones CharField)."""
    if texto is None:
        return ''
    texto = str(texto)
    return texto if len(texto) <= maximo else texto[: maximo - 1].rstrip() + '…'

# ---------------------------------------------------------------------------
# Lectura
# ---------------------------------------------------------------------------


def leer_filas(sql, params=None):
    """Ejecuta un SELECT calificado y devuelve lista de dicts por fila."""
    with connection.cursor() as cursor:
        cursor.execute(sql, params or [])
        columnas = [col[0] for col in cursor.description]
        return [dict(zip(columnas, fila)) for fila in cursor.fetchall()]


def contar(sql, params=None):
    """Devuelve un escalar (conteo) de la BD del catálogo."""
    with connection.cursor() as cursor:
        cursor.execute(sql, params or [])
        return cursor.fetchone()[0]


SQL_ITEMS_CLASIFICADOR = """
SELECT item_uuid, codigo, denominacion, descripcion, sigla, parent_uuid,
       nivel, estado_homologacion, atributos_json, archivo_origen
FROM catalogo.clasificador_item
WHERE clasificador_codigo = %s AND gestion = %s
"""


def leer_items_clasificador(clasificador_codigo, gestion):
    """Lee los ítems de un clasificador del catálogo maestro."""
    return leer_filas(SQL_ITEMS_CLASIFICADOR, [clasificador_codigo, gestion])


# ---------------------------------------------------------------------------
# Jerarquías BFS
# ---------------------------------------------------------------------------


def orden_bfs(filas, key='item_uuid', parent_key='parent_uuid'):
    """Ordena filas jerárquicas BFS: padres siempre antes que hijos.

    Devuelve la lista reordenada. Las filas cuyo ``parent_uuid`` no aparece
    en el conjunto (huérfanas) se agregan al final para no perderlas.
    """
    hijos = defaultdict(list)
    for fila in filas:
        hijos[fila.get(parent_key)].append(fila)

    resultado = []
    vistos = set()
    cola = list(hijos.get(None, []))
    while cola:
        fila = cola.pop(0)
        if fila[key] in vistos:
            continue
        vistos.add(fila[key])
        resultado.append(fila)
        cola.extend(hijos.get(fila[key], []))

    for fila in filas:
        if fila[key] not in vistos:
            resultado.append(fila)
    return resultado


def profundidad(fila, filas_por_uuid, parent_key='parent_uuid'):
    """Profundidad de la fila siguiendo la cadena de parent_uuid."""
    profundidad = 1
    actual = fila
    vistos = set()
    while actual.get(parent_key) and actual[parent_key] not in vistos:
        vistos.add(actual[parent_key])
        actual = filas_por_uuid.get(actual[parent_key])
        if actual is None:
            break
        profundidad += 1
    return profundidad


# ---------------------------------------------------------------------------
# Upsert idempotente
# ---------------------------------------------------------------------------


def upsert(modelo, claves, valores, reporte, campos_actualizables=None):
    """get_or_create por ``claves``; actualiza solo campos no semánticos.

    - ``creados``: filas nuevas.
    - ``actualizados``: filas existentes cuyo contenido cambió.
    - ``omitidos``: filas existentes idénticas (re-ejecución).
    No reemplaza asociaciones semánticas existentes. Una fila legacy sin
    versión puede vincularse una sola vez a la versión de su misma gestión.
    """
    obj, creado = modelo.objects.get_or_create(defaults=valores, **claves)
    if creado:
        reporte.creados += 1
        return obj

    if campos_actualizables is None:
        campos_actualizables = set(valores.keys())
    cambios = {
        k: v for k, v in valores.items()
        if k in campos_actualizables and getattr(obj, k) != v
    }
    # Existing legacy rows are deliberately nullable for compatibility. They
    # may be attached once, and only to a version for the same fiscal year;
    # an existing semantic association is never replaced.
    version_nueva = valores.get('version_clasificador')
    if (
        version_nueva is not None
        and getattr(obj, 'version_clasificador_id', None) is None
        and getattr(obj, 'gestion_id', None) == version_nueva.gestion_id
    ):
        cambios['version_clasificador'] = version_nueva
    if cambios:
        for k, v in cambios.items():
            setattr(obj, k, v)
        obj.save(update_fields=list(cambios))
        reporte.actualizados += 1
    else:
        reporte.omitidos += 1
    return obj


def zfill_codigo(valor, ancho):
    """Normaliza un código a ancho fijo de dígitos (FF 2, OF 3, OG 5...)."""
    if valor is None:
        return ''
    texto = str(valor).strip()
    return texto.zfill(ancho) if texto.isdigit() else texto


# ---------------------------------------------------------------------------
# Versiones de clasificador
# ---------------------------------------------------------------------------


def version_clasificador(tipo, gestion, procedencia):
    """Reutiliza la versión existente o crea una NO vigente (incierta).

    Nunca marca vigente: la vigencia exige fuente oficial completa (RM 249
    para 2026 ya sembrada; la homologación 2027 queda fuera de alcance).
    """
    gestion_fiscal = resolver_gestion(gestion)
    version = VersionClasificador.objects.filter(
        tipo=tipo, gestion=gestion_fiscal,
    ).first()
    if version is not None:
        return version
    return VersionClasificador.objects.create(
        tipo=tipo,
        gestion=gestion_fiscal,
        norma='',
        fecha_norma=None,
        codigo_fuente='',
        procedencia_normativa=procedencia,
        hash_fuente='',
        clasificacion_fuente=VersionClasificador.FUENTE_INCIERTA,
        vigente=False,
    )


# ---------------------------------------------------------------------------
# Reporte
# ---------------------------------------------------------------------------


@dataclass
class ReporteLote:
    lote: str
    fuente: str = ''
    creados: int = 0
    actualizados: int = 0
    omitidos: int = 0
    errores: int = 0
    warnings: list = field(default_factory=list)
    conteos_modelo: dict = field(default_factory=dict)

    def to_dict(self):
        return asdict(self)


def reconciliar_item_origen(reporte):
    """Compara clasificador_item vs clasificador_item_origen (H4/R8).

    La fuente de verdad es ``clasificador_item``; las filas extra del origen
    (6 en OBJETO_GASTO: 511 vs 505) se reportan como warning sin importarse.
    """
    items = {
        fila['clasificador_codigo']: fila['total']
        for fila in leer_filas(
            'SELECT clasificador_codigo, count(*) AS total '
            'FROM catalogo.clasificador_item GROUP BY clasificador_codigo'
        )
    }
    origen = {
        fila['clasificador_codigo']: fila['total']
        for fila in leer_filas(
            'SELECT clasificador_codigo, count(*) AS total '
            'FROM catalogo.clasificador_item_origen '
            'GROUP BY clasificador_codigo'
        )
    }
    for clasificador, total in sorted(items.items()):
        total_origen = origen.get(clasificador, 0)
        if total_origen != total:
            reporte.warnings.append(
                f'Reconciliación {clasificador}: clasificador_item={total} '
                f'vs clasificador_item_origen={total_origen} '
                f'(diferencia {total_origen - total:+d}, no importada)'
            )
