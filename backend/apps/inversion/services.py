from decimal import Decimal
from django.db import transaction
from django.db.models import Sum

from .models import (
    ProyectoInversion, ProgramacionPlurianualProyecto,
    ProgramacionFisicaFinanciera,
)


@transaction.atomic
def crear_proyecto(data):
    proyecto = ProyectoInversion.objects.create(
        codigo_interno=data['codigo_interno'],
        nombre=data['nombre'],
        tipo_id=data.get('tipo_id'),
        prioridad=data.get('prioridad', 4),
        etapa=data.get('etapa', 'preinversion'),
        ue_id=data['ue_id'],
        programa_id=data['programa_id'],
        fuente_id=data['fuente_id'],
        organismo_id=data.get('organismo_id'),
        costo_total=data['costo_total'],
        gestion_inicio=data['gestion_inicio'],
        gestion_fin=data.get('gestion_fin'),
        descripcion=data.get('descripcion', ''),
        codigo_sisin=data.get('codigo_sisin', ''),
    )
    return proyecto


def cambiar_estado_proyecto(proyecto_id, nuevo_estado, motivo=''):
    transiciones_validas = {
        'preinversion': ['inversion'],
        'inversion': ['cierre'],
        'cierre': ['operacion'],
    }
    try:
        proyecto = ProyectoInversion.objects.get(id=proyecto_id)
    except ProyectoInversion.DoesNotExist:
        return {'exito': False, 'mensaje': 'Proyecto no encontrado.'}
    permitidos = transiciones_validas.get(proyecto.etapa, [])
    if nuevo_estado not in permitidos:
        return {
            'exito': False,
            'mensaje': (
                'No se puede cambiar de "'
                + proyecto.get_etapa_display()
                + '" a "'
                + nuevo_estado
                + '". Estados validos: '
                + str(permitidos)
            ),
        }
    proyecto.etapa = nuevo_estado
    proyecto.save(update_fields=['etapa', 'updated_at'])
    return {'exito': True, 'mensaje': 'Estado cambiado a ' + nuevo_estado}


def validar_tecnico(proyecto_id):
    try:
        proyecto = ProyectoInversion.objects.get(id=proyecto_id)
    except ProyectoInversion.DoesNotExist:
        return {'valido': False, 'mensaje': 'Proyecto no encontrado.'}
    errores = []
    if not proyecto.codigo_interno:
        errores.append('Falta codigo interno.')
    if not proyecto.nombre:
        errores.append('Falta nombre del proyecto.')
    if not proyecto.ue_id:
        errores.append('Falta unidad ejecutora.')
    if proyecto.costo_total <= 0:
        errores.append('El costo total debe ser mayor a cero.')
    if not proyecto.gestion_inicio:
        errores.append('Falta gestion de inicio.')
    if not proyecto.fuente_id:
        errores.append('Falta fuente de financiamiento.')
    if not proyecto.programa_id:
        errores.append('Falta programa presupuestario.')
    return {'valido': len(errores) == 0, 'errores': errores}


def calcular_avance_fisico(proyecto_id, gestion=None):
    try:
        proyecto = ProyectoInversion.objects.get(id=proyecto_id)
    except ProyectoInversion.DoesNotExist:
        return None
    if gestion:
        programaciones = ProgramacionFisicaFinanciera.objects.filter(
            proyecto=proyecto, gestion=gestion
        )
    else:
        programaciones = ProgramacionFisicaFinanciera.objects.filter(proyecto=proyecto)
    total_programado = programaciones.aggregate(
        total=Sum('monto_programado')
    )['total'] or Decimal('0')
    if proyecto.costo_total > 0 and total_programado > 0:
        avance = (proyecto.ejecucion_acumulada / total_programado * 100).quantize(Decimal('0.01'))
    else:
        avance = Decimal('0')
    return {
        'proyecto_id': str(proyecto.id),
        'costo_total': proyecto.costo_total,
        'ejecucion_acumulada': proyecto.ejecucion_acumulada,
        'monto_programado': total_programado,
        'avance_porcentaje': avance,
        'etapa': proyecto.etapa,
    }


def crear_programacion_plurianual(proyecto_id, anios_data):
    resultados = []
    for item in anios_data:
        prog, _ = ProgramacionPlurianualProyecto.objects.update_or_create(
            proyecto_id=proyecto_id,
            anio=item['anio'],
            defaults={'monto_programado': item['monto']},
        )
        resultados.append(prog)
    return resultados


def crear_programacion_fisica_financiera(proyecto_id, gestion, data):
    prog, _ = ProgramacionFisicaFinanciera.objects.update_or_create(
        proyecto_id=proyecto_id,
        gestion=gestion,
        defaults=data,
    )
    return prog


def calcular_total_programacion_plurianual(proyecto_id):
    total = ProgramacionPlurianualProyecto.objects.filter(
        proyecto_id=proyecto_id
    ).aggregate(total=Sum('monto_programado'))['total'] or Decimal('0')
    try:
        proyecto = ProyectoInversion.objects.get(id=proyecto_id)
    except ProyectoInversion.DoesNotExist:
        return {'total_programado': total, 'costo_total': Decimal('0'), 'coincide': False}
    return {
        'total_programado': total,
        'costo_total': proyecto.costo_total,
        'coincide': total == proyecto.costo_total,
    }
