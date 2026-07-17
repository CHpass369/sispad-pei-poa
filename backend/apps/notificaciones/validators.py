def validar_tipo_notificacion(tipo_codigo):
    from apps.notificaciones.models import TipoNotificacion
    if not tipo_codigo or not tipo_codigo.strip():
        return {'valido': False, 'mensaje': 'El codigo del tipo de notificacion es requerido.'}
    if not TipoNotificacion.objects.filter(codigo=tipo_codigo, is_active=True).exists():
        return {
            'valido': False,
            'mensaje': 'El tipo de notificacion "' + tipo_codigo + '" no existe o esta inactivo.',
        }
    return {'valido': True, 'mensaje': 'Tipo de notificacion valido.'}


def validar_destinatario(usuario):
    if usuario is None:
        return {'valido': False, 'mensaje': 'El destinatario es requerido.'}
    if not usuario.is_active:
        return {'valido': False, 'mensaje': 'El destinatario no esta activo.'}
    from apps.notificaciones.models import PreferenciaNotificacion
    preferencia = PreferenciaNotificacion.objects.filter(user=usuario).first()
    if preferencia and not preferencia.receive_internal:
        return {
            'valido': True,
            'mensaje': 'El usuario tiene deshabilitadas las notificaciones internas.',
            'advertencia': True,
        }
    return {'valido': True, 'mensaje': 'Destinatario valido.'}
