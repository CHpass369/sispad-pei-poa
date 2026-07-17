def validar_solicitud_borrador(solicitud):
    if solicitud is None:
        return {'valido': False, 'mensaje': 'La solicitud no existe.'}
    if solicitud.estado != 'borrador':
        return {
            'valido': False,
            'mensaje': (
                'La solicitud esta en estado "'
                + solicitud.get_estado_display()
                + '". Solo se puede editar en borrador.'
            ),
        }
    return {'valido': True, 'mensaje': 'Solicitud en borrador, editable.'}


def validar_cambio_tipo(solicitud, cambios):
    if not cambios:
        return {'valido': False, 'mensaje': 'Debe especificar al menos un cambio.'}
    tipos_numericos = [
        'impacto_financiero', 'meta_fisica', 'presupuesto',
        'monto_programado', 'monto_estimado', 'costo_total',
    ]
    for cambio in cambios:
        campo = cambio.get('campo', '')
        valor_anterior = cambio.get('valor_anterior', '')
        valor_propuesto = cambio.get('valor_propuesto', '')
        if campo in tipos_numericos:
            try:
                float(valor_propuesto)
            except (TypeError, ValueError):
                return {
                    'valido': False,
                    'mensaje': 'El campo "' + campo + '" debe ser numerico.',
                }
    return {'valido': True, 'mensaje': 'Tipos de cambio validos.'}


def validar_justificacion_requerida(solicitud):
    if not solicitud.motivo or not solicitud.motivo.strip():
        return {'valido': False, 'mensaje': 'El motivo/justificacion es obligatorio.'}
    if len(solicitud.motivo) < 20:
        return {
            'valido': False,
            'mensaje': 'El motivo debe tener al menos 20 caracteres.',
        }
    return {'valido': True, 'mensaje': 'Justificacion completa.'}
