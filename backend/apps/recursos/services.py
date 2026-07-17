from decimal import Decimal
from django.db.models import Sum

from .models import EstimacionRecurso, EstimacionPlurianual


def calcular_disponibilidad(fuente_id, gestion, organismo_id=None):
    from apps.techos.models import TechoPresupuestario
    techos_qs = TechoPresupuestario.objects.filter(
        fuente_id=fuente_id, gestion=gestion, activo=True
    )
    if organismo_id:
        techos_qs = techos_qs.filter(organismo_id=organismo_id)
    total_techo = techos_qs.aggregate(total=Sum('monto_total'))['total'] or Decimal('0')

    from apps.presupuesto.models import LineaPresupuestaria
    lineas_qs = LineaPresupuestaria.objects.filter(
        fuente_id=fuente_id, gestion=gestion, activo=True
    )
    if organismo_id:
        lineas_qs = lineas_qs.filter(organismo_id=organismo_id)
    total_comprometido = lineas_qs.aggregate(total=Sum('importe'))['total'] or Decimal('0')

    disponible = total_techo - total_comprometido
    return {
        'total_techo': total_techo,
        'total_comprometido': total_comprometido,
        'disponible': disponible,
        'porcentaje_ejecutado': (
            (total_comprometido / total_techo * 100).quantize(Decimal('0.01'))
            if total_techo > 0 else Decimal('0')
        ),
    }


def asignar_recurso(fuente_id, organismo_id, gestion, monto, memoria_calculo=''):
    estimacion = EstimacionRecurso.objects.create(
        gestion=gestion,
        rubro_id=fuente_id,
        fuente_id=fuente_id,
        organismo_id=organismo_id,
        monto_estimado=monto,
        memoria_calculo=memoria_calculo,
    )
    return estimacion


def liberar_recurso(estimacion_id, monto_liberar):
    try:
        estimacion = EstimacionRecurso.objects.get(id=estimacion_id)
    except EstimacionRecurso.DoesNotExist:
        return {'exito': False, 'mensaje': 'La estimación no existe.'}
    if monto_liberar > estimacion.monto_estimado:
        return {
            'exito': False,
            'mensaje': f'El monto a liberar ({monto_liberar}) excede el monto estimado ({estimacion.monto_estimado}).',
        }
    estimacion.monto_estimado -= monto_liberar
    estimacion.save(update_fields=['monto_estimado', 'actualizado_en'])
    return {'exito': True, 'mensaje': f'Recurso liberado. Nuevo saldo: Bs {estimacion.monto_estimado}'}


def validar_solapamiento(fuente_id, gestion, monto, exclude_id=None):
    overlaps = EstimacionRecurso.objects.filter(
        fuente_id=fuente_id, gestion=gestion, activo=True
    )
    if exclude_id:
        overlaps = overlaps.exclude(id=exclude_id)
    total_existente = overlaps.aggregate(total=Sum('monto_estimado'))['total'] or Decimal('0')
    from apps.techos.models import TechoPresupuestario
    techo = TechoPresupuestario.objects.filter(
        fuente_id=fuente_id, gestion=gestion, activo=True
    ).aggregate(total=Sum('monto_total'))['total'] or Decimal('0')
    nuevo_total = total_existente + monto
    if nuevo_total > techo:
        return {
            'valido': False,
            'mensaje': (
                f'El monto total (Bs {nuevo_total}) excede el techo presupuestario '
                f'(Bs {techo}). Disponible: Bs {techo - total_existente}.'
            ),
        }
    return {'valido': True, 'mensaje': 'Solapamiento válido.'}


def obtener_estimaciones_por_gestion(gestion):
    return EstimacionRecurso.objects.filter(
        gestion=gestion, activo=True
    ).select_related('rubro', 'fuente', 'organismo').order_by('rubro__codigo')


def crear_estimacion_plurianual(estimacion_origen, anios_data):
    resultados = []
    for item in anios_data:
        proyeccion, created = EstimacionPlurianual.objects.update_or_create(
            estimacion_origen=estimacion_origen,
            anio=item['anio'],
            defaults={'monto_proyectado': item['monto']},
        )
        resultados.append(proyeccion)
    return resultados
