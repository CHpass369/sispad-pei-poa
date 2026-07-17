TRANSICIONES_PERMITIDAS = {
    'borrador': ['enviar'],
    'enviado': ['aprobar', 'observar'],
    'en_revision': ['aprobar', 'observar'],
    'observado': ['subsanar'],
    'aprobado': ['consolidar'],
    'consolidado': ['aprobar_final'],
}


def validar_transicion_estado(estado_actual, nuevo_estado):
    permitidos = TRANSICIONES_PERMITIDAS.get(estado_actual, [])
    if nuevo_estado not in permitidos:
        return {
            'valido': False,
            'mensaje': (
                'Transicion de "' + estado_actual + '" a "' + nuevo_estado
                + '" no permitida. Acciones validas: ' + str(permitidos)
            ),
        }
    return {'valido': True, 'mensaje': 'Transicion valida.'}


def validar_permiso_usuario(usuario, estado_actual, accion):
    from apps.core.permissions import TRANSICIONES_WORKFLOW, _user_has_role
    transiciones = TRANSICIONES_WORKFLOW.get(estado_actual, {})
    roles = transiciones.get(accion, [])
    if not roles:
        return {
            'valido': False,
            'mensaje': 'Accion "' + accion + '" no definida para estado "' + estado_actual + '".',
        }
    if _user_has_role(usuario, *roles):
        return {'valido': True, 'mensaje': 'Usuario tiene permiso.'}
    return {
        'valido': False,
        'mensaje': 'El usuario no tiene los roles requeridos: ' + ', '.join(roles),
    }


def validar_documento_adjunto(envio):
    from apps.documentos.models import DocumentoAdjunto
    docs = DocumentoAdjunto.objects.filter(
        entidad='EnvioFormulacion',
        entidad_id=str(envio.pk),
        activo=True,
    )
    if not docs.exists():
        return {
            'valido': False,
            'mensaje': 'El envio no tiene documentos adjuntos.',
        }
    return {'valido': True, 'mensaje': 'Documentos adjuntos presentes.'}
