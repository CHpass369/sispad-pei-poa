from django.db import transaction
from django.utils import timezone

from .models import EnvioFormulacion, Revision, Observacion, Aprobacion


@transaction.atomic
def enviar_aprobacion(unidad_id, gestion, version, usuario, comentario=''):
    envio = EnvioFormulacion.objects.create(
        unidad_id=unidad_id,
        gestion=gestion,
        version=version,
        enviado_por=usuario,
        comentario=comentario,
        estado_anterior='borrador',
    )
    return envio


@transaction.atomic
def aprobar(envio_id, usuario, resultado='aprobado', comentario=''):
    try:
        envio = EnvioFormulacion.objects.get(id=envio_id)
    except EnvioFormulacion.DoesNotExist:
        return {'exito': False, 'mensaje': 'Envio no encontrado.'}
    revision = Revision.objects.filter(
        envio=envio, estado__in=['pendiente', 'en_curso']
    ).first()
    if revision:
        revision.estado = 'completada'
        revision.resultado = resultado
        revision.revisor = usuario
        revision.fecha_completado = timezone.now()
        revision.save(update_fields=[
            'estado', 'resultado', 'revisor', 'fecha_completado', 'updated_at'
        ])
    return {'exito': True, 'mensaje': 'Aprobacion registrada.'}


@transaction.atomic
def observar(revision_id, usuario, texto, tipo='fondo', severidad='moderada'):
    try:
        revision = Revision.objects.get(id=revision_id)
    except Revision.DoesNotExist:
        return {'exito': False, 'mensaje': 'Revision no encontrada.'}
    import uuid
    codigo = 'OBS-' + str(uuid.uuid4())[:8].upper()
    observacion = Observacion.objects.create(
        codigo=codigo,
        revision=revision,
        tipo=tipo,
        severidad=severidad,
        modulo='',
        registro_id=str(revision.envio_id),
        texto=texto,
        responsable_subsanacion=revision.envio.enviado_por,
        gestion=revision.envio.gestion,
    )
    revision.estado = 'devuelta'
    revision.resultado = 'observado'
    revision.save(update_fields=['estado', 'resultado', 'updated_at'])
    return {'exito': True, 'observacion': observacion}


@transaction.atomic
def subsanar(observacion_id, usuario, respuesta, evidencia=''):
    try:
        observacion = Observacion.objects.get(id=observacion_id)
    except Observacion.DoesNotExist:
        return {'exito': False, 'mensaje': 'Observacion no encontrada.'}
    observacion.respuesta = respuesta
    observacion.evidencia_subsanacion = evidencia
    observacion.estado = 'aceptada'
    observacion.save(update_fields=[
        'respuesta', 'evidencia_subsanacion', 'estado', 'updated_at'
    ])
    return {'exito': True, 'mensaje': 'Observacion subsanada.'}


def consolidar_poa(gestion, version, usuario):
    from apps.poau.models import POAU
    poaus = POAU.objects.filter(gestion=gestion, estado='aprobado')
    total = poaus.count()
    aprobacion = Aprobacion.objects.create(
        gestion=gestion,
        tipo='consolidacion',
        aprobado_por=usuario,
        estado='aprobado',
        version=version,
        comentario='Consolidacion institucional del POA',
    )
    return {
        'exito': True,
        'total_poaus': total,
        'aprobacion_id': str(aprobacion.id),
    }


def verificar_permisos_estado(usuario, estado_actual, accion):
    from apps.core.permissions import TRANSICIONES_WORKFLOW, _user_has_role
    transiciones = TRANSICIONES_WORKFLOW.get(estado_actual, {})
    roles_permitidos = transiciones.get(accion, [])
    if not roles_permitidos:
        return {
            'permitido': False,
            'mensaje': 'Accion "' + accion + '" no permitida desde estado "' + estado_actual + '".',
        }
    if _user_has_role(usuario, *roles_permitidos):
        return {'permitido': True, 'mensaje': 'Accion permitida.'}
    return {
        'permitido': False,
        'mensaje': 'El usuario no tiene el rol requerido para esta accion.',
    }


def obtener_envios_por_gestion(gestion):
    return EnvioFormulacion.objects.filter(
        gestion=gestion, activo=True
    ).select_related('unidad', 'enviado_por').order_by('-fecha_envio')


def obtener_observaciones_pendientes(gestion):
    return Observacion.objects.filter(
        gestion=gestion, estado='abierta'
    ).select_related('revision', 'responsable_subsanacion').order_by('-created_at')
