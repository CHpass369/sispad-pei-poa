from decimal import Decimal
from django.db.models import Sum
from django.db import transaction

from .models import (
    LineaPresupuestaria, ProgramaPresupuestario,
    ProyectoPresupuestario, ActividadPresupuestaria,
)


def validar_disponibilidad(ue_id, fuente_id, gestion, monto, exclude_id=None):
    from apps.techos.models import DistribucionTecho, TechoPresupuestario
    techo_qs = TechoPresupuestario.objects.filter(
        fuente_id=fuente_id, gestion=gestion, activo=True
    )
    distribucion_qs = DistribucionTecho.objects.filter(
        techo__in=techo_qs, ue_id=ue_id, activo=True
    )
    techo_total = distribucion_qs.aggregate(
        total=Sum('monto_asignado')
    )['total'] or Decimal('0')

    lineas_qs = LineaPresupuestaria.objects.filter(
        ue_id=ue_id, fuente_id=fuente_id, gestion=gestion, activo=True
    )
    if exclude_id:
        lineas_qs = lineas_qs.exclude(id=exclude_id)
    total_asignado = lineas_qs.aggregate(total=Sum('importe'))['total'] or Decimal('0')

    disponible = techo_total - total_asignado
    if monto > disponible:
        return {
            'valido': False,
            'mensaje': (
                f'El monto (Bs {monto}) excede la disponibilidad '
                f'(Bs {disponible}). Techo: Bs {techo_total}, '
                f'ya asignado: Bs {total_asignado}.'
            ),
            'disponible': disponible,
        }
    return {'valido': True, 'mensaje': 'Disponibilidad confirmada.', 'disponible': disponible}


@transaction.atomic
def registrar_compromiso(linea_data):
    linea = LineaPresupuestaria.objects.create(**linea_data)
    return linea


@transaction.atomic
def registrar_devengado(linea_id, monto_devengado):
    try:
        linea = LineaPresupuestaria.objects.get(id=linea_id)
    except LineaPresupuestaria.DoesNotExist:
        return {'exito': False, 'mensaje': 'Línea presupuestaria no encontrada.'}
    return {'exito': True, 'linea': linea, 'monto_devengado': monto_devengado}


def calcular_saldo(gestion, ue_id=None, fuente_id=None, programa_id=None):
    qs = LineaPresupuestaria.objects.filter(gestion=gestion, activo=True)
    if ue_id:
        qs = qs.filter(ue_id=ue_id)
    if fuente_id:
        qs = qs.filter(fuente_id=fuente_id)
    if programa_id:
        qs = qs.filter(programa_id=programa_id)
    total = qs.aggregate(total=Sum('importe'))['total'] or Decimal('0')

    from apps.techos.models import DistribucionTecho, TechoPresupuestario
    techo_qs = TechoPresupuestario.objects.filter(gestion=gestion, activo=True)
    if fuente_id:
        techo_qs = techo_qs.filter(fuente_id=fuente_id)
    distribucion_qs = DistribucionTecho.objects.filter(techo__in=techo_qs, activo=True)
    if ue_id:
        distribucion_qs = distribucion_qs.filter(ue_id=ue_id)
    techo_total = distribucion_qs.aggregate(
        total=Sum('monto_asignado')
    )['total'] or Decimal('0')

    return {
        'gestion': gestion,
        'total_asignado': total,
        'techo_total': techo_total,
        'saldo_disponible': techo_total - total,
    }


def validar_lineas_igual_total(gestion, ue_id=None):
    from apps.core.validators import validar_lineas_igual_total as _validar
    qs = LineaPresupuestaria.objects.filter(gestion=gestion, activo=True)
    if ue_id:
        qs = qs.filter(ue_id=ue_id)
    lineas = list(qs.values('id', 'importe'))
    total_programado = qs.aggregate(total=Sum('importe'))['total'] or Decimal('0')
    return _validar(
        [{'monto': l['importe']} for l in lineas],
        total_programado,
    )


def obtener_lineas_por_programa(gestion, programa_id):
    return LineaPresupuestaria.objects.filter(
        gestion=gestion, programa_id=programa_id, activo=True
    ).select_related('ue', 'fuente', 'objeto_gasto').order_by('programa__codigo')


def crear_programa_presupuestario(codigo, nombre, gestion, ue_responsable_id=None):
    programa = ProgramaPresupuestario.objects.create(
        codigo=codigo,
        nombre=nombre,
        gestion=gestion,
        ue_responsable_id=ue_responsable_id,
    )
    return programa


def crear_proyecto_presupuestario(codigo, nombre, programa_id, gestion):
    proyecto = ProyectoPresupuestario.objects.create(
        codigo=codigo,
        nombre=nombre,
        programa_id=programa_id,
        gestion=gestion,
    )
    return proyecto


def crear_actividad_presupuestaria(codigo, nombre, proyecto_id, gestion):
    actividad = ActividadPresupuestaria.objects.create(
        codigo=codigo,
        nombre=nombre,
        proyecto_id=proyecto_id,
        gestion=gestion,
    )
    return actividad
