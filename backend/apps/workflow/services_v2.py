"""Servicios del workflow configurable V2 (WP-08)."""
from datetime import date

from django.utils import timezone

from apps.accounts.permissions import tiene_capacidad
from apps.workflow.models_v2 import (
    EstadosTarea,
    WorkflowAprobacion,
    WorkflowDefinition,
    WorkflowInstance,
    WorkflowObservacion,
    WorkflowStepDefinition,
    WorkflowTask,
    WorkflowTransition,
)


def _verificar_capacidades(usuario, capacidades):
    """Retorna error si el usuario no posee ninguna capacidad requerida."""
    if not capacidades:
        return None
    if any(tiene_capacidad(usuario, c) for c in capacidades):
        return None
    return f'Requiere una de las capacidades: {", ".join(capacidades)}'


def iniciar_workflow(codigo_definicion, entidad_tipo, entidad_id, usuario):
    """Crea una instancia de workflow y su primera tarea."""
    definicion = WorkflowDefinition.objects.filter(
        codigo=codigo_definicion, activo=True,
    ).first()
    if not definicion:
        return None, f'Definición de workflow "{codigo_definicion}" no encontrada.'

    paso_inicial = definicion.pasos.filter(es_inicial=True).first()
    if not paso_inicial:
        return None, 'La definición no tiene paso inicial.'

    try:
        instancia = WorkflowInstance.objects.create(
            definicion=definicion,
            entidad_tipo=entidad_tipo,
            entidad_id=entidad_id,
            estado_actual=paso_inicial.estado,
            paso_actual=paso_inicial,
            iniciado_por=usuario,
        )
    except Exception:
        return None, (
            'La entidad ya tiene una instancia de workflow abierta para '
            'esta definición.'
        )
    WorkflowTask.objects.create(
        instancia=instancia,
        paso=paso_inicial,
        asignado_a=usuario,
        estado=EstadosTarea.EN_CURSO,
    )
    return instancia, None


def tarea_actual(instancia):
    return instancia.tareas.filter(
        estado__in=[EstadosTarea.PENDIENTE, EstadosTarea.EN_CURSO],
    ).order_by('-creado_en').first()


def _transicion_disponible(instancia, usuario):
    tarea = tarea_actual(instancia)
    if not tarea:
        return None, None, 'No hay tarea en curso para la instancia.'
    transicion = WorkflowTransition.objects.filter(
        definicion=instancia.definicion,
        desde_paso=tarea.paso,
    ).first()
    if not transicion and tarea.paso.es_inicial:
        # Paso inicial: la transición de salida se declara desde el inicio
        transicion = WorkflowTransition.objects.filter(
            definicion=instancia.definicion,
            desde_paso__isnull=True,
        ).first()
    if not transicion:
        return None, tarea, 'No hay transición configurada desde este paso.'
    error = _verificar_capacidades(usuario, transicion.capacidades_requeridas)
    if error:
        return None, tarea, error
    return transicion, tarea, None


def _completar_tarea(tarea):
    tarea.estado = EstadosTarea.COMPLETADA
    tarea.completado_en = timezone.now()
    tarea.save(update_fields=['estado', 'completado_en'])


def avanzar_workflow(instancia, usuario, comentario=''):
    """Avanza la instancia a la siguiente tarea/paso configurado."""
    transicion, tarea, error = _transicion_disponible(instancia, usuario)
    if error:
        return False, error
    _completar_tarea(tarea)
    siguiente = transicion.hacia_paso
    instancia.paso_actual = siguiente
    instancia.estado_actual = siguiente.estado
    instancia.save(update_fields=['paso_actual', 'estado_actual'])
    if siguiente.es_final:
        instancia.cerrado = True
        instancia.cerrado_en = timezone.now()
        instancia.save(update_fields=['cerrado', 'cerrado_en'])
    else:
        WorkflowTask.objects.create(
            instancia=instancia, paso=siguiente, asignado_a=usuario,
            estado=EstadosTarea.EN_CURSO,
        )
    return True, transicion


def aprobar_workflow(instancia, usuario, comentario='', entidad_destino=None):
    """Avanza registrando la aprobación; opcionalmente sincroniza la entidad
    destino (p. ej. VersionInstrumento.aprobar) en el paso final."""
    ok, resultado = avanzar_workflow(instancia, usuario, comentario)
    if not ok:
        return False, resultado
    tarea = instancia.tareas.order_by('-creado_en').first()
    WorkflowAprobacion.objects.create(
        instancia=instancia,
        tarea=tarea,
        aprobado_por=usuario,
        resultado='aprobado',
        comentario=comentario,
    )
    if instancia.cerrado and entidad_destino is not None:
        if not getattr(entidad_destino, 'inmutable', False):
            entidad_destino.aprobar(usuario=usuario, norma=comentario or 'Aprobado por workflow')
    return True, None


def observar_workflow(instancia, usuario, texto, severidad='moderada'):
    """Registra observación, rechaza la tarea actual y deja la instancia
    en el mismo paso para subsanar (nueva tarea)."""
    tarea = tarea_actual(instancia)
    if not tarea:
        return False, 'No hay tarea en curso para la instancia.'
    tarea.estado = EstadosTarea.RECHAZADA
    tarea.save(update_fields=['estado'])
    WorkflowObservacion.objects.create(
        instancia=instancia,
        tarea=tarea,
        usuario=usuario,
        texto=texto,
        severidad=severidad,
    )
    WorkflowAprobacion.objects.create(
        instancia=instancia,
        tarea=tarea,
        aprobado_por=usuario,
        resultado='observado',
        comentario=texto[:300],
    )
    WorkflowTask.objects.create(
        instancia=instancia, paso=tarea.paso, asignado_a=tarea.asignado_a,
        estado=EstadosTarea.EN_CURSO,
    )
    return True, None


def delegar_tarea(tarea, delegado_de, delegado_a, motivo='', vigente_hasta=None):
    """Registra una delegación y reasigna la tarea."""
    from apps.workflow.models_v2 import Delegacion

    delegacion = Delegacion.objects.create(
        tarea=tarea,
        delegado_de=delegado_de,
        delegado_a=delegado_a,
        motivo=motivo,
        vigente_hasta=vigente_hasta,
    )
    tarea.asignado_a = delegado_a
    tarea.save(update_fields=['asignado_a'])
    return delegacion
