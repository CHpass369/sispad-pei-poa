"""Lo priorizado y validado se vuelca al Presupuesto General de Gastos.

Al validarse, el acta deja de ser una intención: su monto tiene que aparecer en
la fila de gasto de la categoría programática que le corresponde, contra el par
FF/OF elegido. De ahí sale el descuento del techo.

Si después se observa, el volcado se revierte: un acta devuelta para corrección
no puede seguir ocupando techo en el presupuesto de gastos.

La operación es idempotente. `AperturaFuente` tiene un único registro por
(apertura, fuente, organismo), así que dos proyectos con la misma categoría y
el mismo par suman sobre la misma fila; y cada proyecto recuerda cuánto puso,
para que volver a aprobar recalcule en vez de duplicar.
"""
from django.db import transaction

from apps.budget.categoria import partes_categoria
from apps.budget.models import Apertura, AperturaFuente, CategoriaProgramaticaTecho
from apps.gestion.models import GestionFiscal


def _categoria_de(codigo, gestion_fiscal):
    """La categoría del catálogo maestro, si está dada de alta."""
    limpio = partes_categoria(codigo).codigo
    if not limpio:
        return None
    por_gestion = CategoriaProgramaticaTecho.objects.filter(
        codigo__iexact=limpio, gestion=gestion_fiscal)
    return (por_gestion.first()
            or CategoriaProgramaticaTecho.objects.filter(
                codigo__iexact=limpio).first())


def _apertura_de(proyecto, gestion_fiscal, categoria):
    """La fila de gasto de esa categoría, creada si todavía no existe."""
    partes = partes_categoria(proyecto.categoria_programatica)
    apertura = Apertura.objects.filter(
        gestion=gestion_fiscal, categoria=categoria).first()
    if apertura:
        return apertura, False
    return Apertura.objects.create(
        gestion=gestion_fiscal,
        categoria=categoria,
        denominacion=(categoria.denominacion if categoria
                      else proyecto.nombre[:200]),
        proyecto_codigo=partes.programa,
        codigo_sisin=partes.sisin or proyecto.sisin or '',
        actividad_codigo=partes.actividad,
    ), True


def revisar_acta(acta):
    """Qué se puede volcar y qué no, sin escribir nada.

    Se informa proyecto por proyecto: un acta que se aprueba y deja la mitad
    de sus montos afuera en silencio es peor que una que no se aprueba.
    """
    listos, omitidos = [], []
    for proyecto in acta.proyectos.all():
        faltantes = []
        if not proyecto.categoria_programatica:
            faltantes.append('categoría programática')
        if not (proyecto.fuente_id and proyecto.organismo_id):
            faltantes.append('fuente/organismo')
        if not proyecto.monto:
            faltantes.append('monto')
        if faltantes:
            omitidos.append({
                'orden': proyecto.orden, 'nombre': proyecto.nombre,
                'motivo': 'falta ' + ', '.join(faltantes),
            })
        else:
            listos.append(proyecto)
    return listos, omitidos


@transaction.atomic
def materializar_acta(acta):
    """Vuelca al gasto los proyectos del acta que estén completos."""
    gestion_fiscal = GestionFiscal.objects.filter(anio=acta.gestion).first()
    if gestion_fiscal is None:
        return {'materializados': [], 'omitidos': [{
            'orden': 0, 'nombre': '',
            'motivo': f'la gestión fiscal {acta.gestion} no está habilitada',
        }]}

    listos, omitidos = revisar_acta(acta)
    materializados = []

    for proyecto in listos:
        categoria = _categoria_de(proyecto.categoria_programatica, gestion_fiscal)
        if categoria is None:
            omitidos.append({
                'orden': proyecto.orden, 'nombre': proyecto.nombre,
                'motivo': (f'la categoría {proyecto.categoria_programatica} no '
                           'está en el catálogo maestro'),
            })
            continue

        apertura, creada = _apertura_de(proyecto, gestion_fiscal, categoria)
        fila, _ = AperturaFuente.objects.get_or_create(
            allocation=apertura, fuente=proyecto.fuente,
            organismo=proyecto.organismo, defaults={'monto': 0},
        )
        # Se descuenta lo que este mismo proyecto ya había puesto: aprobar dos
        # veces recalcula, no suma de nuevo.
        anterior = proyecto.monto_materializado or 0
        fila.monto = (fila.monto or 0) - anterior + proyecto.monto
        fila.save(update_fields=['monto'])

        proyecto.apertura_fuente = fila
        proyecto.monto_materializado = proyecto.monto
        proyecto.save(update_fields=['apertura_fuente', 'monto_materializado'])

        materializados.append({
            'orden': proyecto.orden,
            'nombre': proyecto.nombre,
            'categoria': categoria.codigo,
            'programa': partes_categoria(categoria.codigo).programa,
            'par': proyecto.par_financiamiento,
            'monto': float(proyecto.monto),
            'apertura_creada': creada,
        })

    return {'materializados': materializados, 'omitidos': omitidos}


@transaction.atomic
def desmaterializar_acta(acta):
    """Deshace el volcado: el acta vuelve a estar solo comprometida.

    Se descuenta exactamente lo que cada proyecto había puesto, no su monto
    actual: entre el volcado y la reversión alguien pudo haber corregido la
    cifra, y descontar la nueva dejaría descuadrada la fila de gasto.
    """
    revertidos = []
    for proyecto in acta.proyectos.exclude(apertura_fuente__isnull=True):
        fila = proyecto.apertura_fuente
        puesto = proyecto.monto_materializado or 0
        fila.monto = (fila.monto or 0) - puesto
        fila.save(update_fields=['monto'])
        revertidos.append({
            'orden': proyecto.orden, 'nombre': proyecto.nombre,
            'monto': float(puesto),
        })
        proyecto.apertura_fuente = None
        proyecto.monto_materializado = None
        proyecto.save(update_fields=['apertura_fuente', 'monto_materializado'])
    return revertidos
