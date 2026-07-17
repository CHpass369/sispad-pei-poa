from django.db.models import Count, Q
from django.utils import timezone
from .models import TipoNotificacion, Notificacion, PreferenciaNotificacion


def crear_notificacion(user, tipo_codigo, titulo, mensaje, **kwargs):
    try:
        tipo = TipoNotificacion.objects.get(codigo=tipo_codigo, is_active=True)
    except TipoNotificacion.DoesNotExist:
        return None

    notificacion = Notificacion.objects.create(
        user=user,
        tipo=tipo,
        titulo=titulo,
        mensaje=mensaje,
        priority=kwargs.get('priority', 'media'),
        entity_type=kwargs.get('entity_type'),
        entity_id=kwargs.get('entity_id'),
        gestion=kwargs.get('gestion', timezone.now().year),
        metadata=kwargs.get('metadata'),
        created_by=kwargs.get('created_by'),
    )
    return notificacion


def notificar_cambio_estado(affected_user, entity_type, entity_id, old_state, new_state, gestion):
    titulo = f'Cambio de estado en {entity_type}'
    mensaje = (
        f'El estado del registro {entity_type} (ID: {entity_id}) '
        f'ha cambiado de "{old_state}" a "{new_state}".'
    )
    return crear_notificacion(
        user=affected_user,
        tipo_codigo='CAMBIO_ESTADO',
        titulo=titulo,
        mensaje=mensaje,
        priority='media',
        entity_type=entity_type,
        entity_id=entity_id,
        gestion=gestion,
        metadata={
            'estado_anterior': old_state,
            'estado_nuevo': new_state,
        },
    )


def notificar_vencimiento(user, entity_type, entity_id, gestion):
    titulo = f'Vencimiento próximo: {entity_type}'
    mensaje = (
        f'La fecha límite para el registro {entity_type} (ID: {entity_id}) '
        f'está próxima a vencer. Gestión {gestion}.'
    )
    return crear_notificacion(
        user=user,
        tipo_codigo='VENCIMIENTO',
        titulo=titulo,
        mensaje=mensaje,
        priority='alta',
        entity_type=entity_type,
        entity_id=entity_id,
        gestion=gestion,
    )


def notificar_observacion(responsable, observacion, gestion):
    titulo = f'Nueva observación: {observacion.codigo}'
    mensaje = (
        f'Se ha registrado la observación {observacion.codigo} '
        f'tipo "{observacion.get_tipo_display()}" con severidad '
        f'"{observacion.get_severidad_display()}". {observacion.texto}'
    )
    return crear_notificacion(
        user=responsable,
        tipo_codigo='OBSERVACION',
        titulo=titulo,
        mensaje=mensaje,
        priority='alta' if observacion.severidad == 'grave' else 'media',
        entity_type='observacion',
        entity_id=observacion.id,
        gestion=gestion,
        metadata={
            'codigo_observacion': observacion.codigo,
            'tipo': observacion.tipo,
            'severidad': observacion.severidad,
        },
    )


def notificar_aprobacion(user, entity_type, entity_id, estado, gestion):
    titulo = f'Aprobación {estado}: {entity_type}'
    mensaje = (
        f'El registro {entity_type} (ID: {entity_id}) '
        f'ha sido {estado} para la gestión {gestion}.'
    )
    return crear_notificacion(
        user=user,
        tipo_codigo='APROBACION',
        titulo=titulo,
        mensaje=mensaje,
        priority='alta' if estado in ('aprobado', 'rechazado') else 'media',
        entity_type=entity_type,
        entity_id=entity_id,
        gestion=gestion,
        metadata={
            'estado_aprobacion': estado,
        },
    )


def obtener_resumen_no_leidas(user):
    qs = Notificacion.objects.filter(user=user, is_read=False)
    conteo = qs.aggregate(
        total=Count('id'),
        alta=Count('id', filter=Q(priority='alta')),
        media=Count('id', filter=Q(priority='media')),
        baja=Count('id', filter=Q(priority='baja')),
    )
    preferencia = PreferenciaNotificacion.objects.filter(user=user).first()
    return {
        'total': conteo['total'],
        'alta': conteo['alta'],
        'media': conteo['media'],
        'baja': conteo['baja'],
        'por_tipo': list(
            qs.values('tipo__codigo', 'tipo__nombre')
            .annotate(cantidad=Count('id'))
            .order_by('-cantidad')
        ),
        'recibir_email': preferencia.receive_email if preferencia else False,
        'frecuencia': preferencia.frequency if preferencia else 'inmediata',
    }
