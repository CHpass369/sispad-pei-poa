ACCIONES_AUDITABLES = [
    'login', 'logout', 'crear', 'modificar', 'anular', 'restaurar',
    'enviar', 'devolver', 'aprobar', 'reabrir', 'importar',
    'exportar', 'consolidar', 'cerrar',
]


def validar_modelo_auditable(modelo):
    if modelo is None:
        return {'valido': False, 'mensaje': 'El modelo es requerido para auditoria.'}
    if not hasattr(modelo, '__class__'):
        return {'valido': False, 'mensaje': 'El objeto no es un modelo valido.'}
    if not hasattr(modelo, '_meta'):
        return {'valido': False, 'mensaje': 'El objeto no es un modelo Django.'}
    return {'valido': True, 'mensaje': 'Modelo auditable.'}


def validar_accion_permitida(accion):
    if accion not in ACCIONES_AUDITABLES:
        return {
            'valido': False,
            'mensaje': (
                'Accion "' + accion + '" no es una accion audit permitida. '
                'Acciones validas: ' + ', '.join(ACCIONES_AUDITABLES)
            ),
        }
    return {'valido': True, 'mensaje': 'Accion audit permitida.'}
