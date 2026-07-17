from decimal import Decimal
from django.db import transaction

from .models import (
    POAU, POAUActividad, EjecucionFisica, EjecucionFinanciera,
)


@transaction.atomic
def crear_poau(unidad_id, gestion, codigo, nombre, **kwargs):
    poau, created = POAU.objects.update_or_create(
        codigo=codigo,
        defaults={
            'unidad_id':unidad_id,
            'gestion':gestion,
            'nombre':nombre,
            'descripcion':kwargs.get('descripcion', ''),
            'estado':kwargs.get('estado', 'borrador'),
            'responsable':kwargs.get('responsable'),
            'producto_territorial_id':kwargs.get('producto_territorial_id'),
        },
    )
    return poau


@transaction.atomic
def agregar_actividad(poau_id, codigo, nombre, **kwargs):
    try:
        poau = POAU.objects.get(id=poau_id)
    except POAU.DoesNotExist:
        return None
    actividad = POAUActividad.objects.create(
        poau=poau,
        codigo=codigo,
        nombre=nombre,
        objeto_gasto_id=kwargs.get('objeto_gasto_id'),
        meta_fisica_anual=kwargs.get('meta_fisica_anual'),
        presupuesto_anual=kwargs.get('presupuesto_anual'),
        meta_q1=kwargs.get('meta_q1'),
        meta_q2=kwargs.get('meta_q2'),
        meta_q3=kwargs.get('meta_q3'),
        meta_q4=kwargs.get('meta_q4'),
        accion_corto_plazo_id=kwargs.get('accion_corto_plazo_id'),
    )
    return actividad


@transaction.atomic
def registrar_ejecucion_fisica(actividad_id, periodo, tipo_periodo, programado, ejecutado, observaciones=''):
    ejecucion, _ = EjecucionFisica.objects.update_or_create(
        actividad_id=actividad_id,
        periodo=periodo,
        defaults={
            'tipo_periodo': tipo_periodo,
            'programado': programado,
            'ejecutado': ejecutado,
            'observaciones': observaciones,
        },
    )
    return ejecucion


@transaction.atomic
def registrar_ejecucion_financiera(actividad_id, periodo, tipo_periodo, programado, ejecutado, observaciones=''):
    ejecucion, _ = EjecucionFinanciera.objects.update_or_create(
        actividad_id=actividad_id,
        periodo=periodo,
        defaults={
            'tipo_periodo': tipo_periodo,
            'programado': programado,
            'ejecutado': ejecutado,
            'observaciones': observaciones,
        },
    )
    return ejecucion


def calcular_avance_trim(poau_id, trimestre):
    try:
        poau = POAU.objects.get(id=poau_id)
    except POAU.DoesNotExist:
        return None
    campo_meta = {
        1: 'meta_q1', 2: 'meta_q2',
        3: 'meta_q3', 4: 'meta_q4',
    }.get(trimestre)
    if not campo_meta:
        return None
    actividades = poau.actividades.all()
    total_programado = Decimal('0')
    total_ejecutado = Decimal('0')
    for act in actividades:
        meta_trim = getattr(act, campo_meta, None)
        if meta_trim:
            total_programado += meta_trim
        filtro_periodo = {
            1: '2026-Q1', 2: '2026-Q2',
            3: '2026-Q3', 4: '2026-Q4',
        }.get(trimestre)
        ef = EjecucionFisica.objects.filter(
            actividad=act, periodo=filtro_periodo
        ).first()
        if ef:
            total_ejecutado += ef.ejecutado or Decimal('0')
    if total_programado > 0:
        avance = (total_ejecutado / total_programado * 100).quantize(Decimal('0.01'))
    else:
        avance = Decimal('0')
    return {
        'trimestre': trimestre,
        'total_programado': total_programado,
        'total_ejecutado': total_ejecutado,
        'avance_porcentaje': avance,
    }


def calcular_semaforo(poau_id):
    try:
        poau = POAU.objects.get(id=poau_id)
    except POAU.DoesNotExist:
        return None
    total_programado = Decimal('0')
    total_ejecutado = Decimal('0')
    for act in poau.actividades.all():
        if act.meta_fisica_anual:
            total_programado += act.meta_fisica_anual
        for ef in EjecucionFisica.objects.filter(actividad=act):
            total_ejecutado += ef.ejecutado or Decimal('0')
    if total_programado > 0:
        avance = (total_ejecutado / total_programado * 100).quantize(Decimal('0.01'))
    else:
        avance = Decimal('0')
    if avance >= Decimal('80'):
        semaforo = 'verde'
    elif avance >= Decimal('50'):
        semaforo = 'amarillo'
    else:
        semaforo = 'rojo'
    return {
        'semaforo': semaforo,
        'avance_porcentaje': avance,
        'total_programado': total_programado,
        'total_ejecutado': total_ejecutado,
    }
