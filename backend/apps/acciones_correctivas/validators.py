from datetime import date


def validar_accion_pendiente(accion):
    if accion is None:
        return {'valido': False, 'mensaje': 'La accion correctiva no existe.'}
    estados_finales = ['cumplida', 'cerrada', 'cancelada']
    if accion.status in estados_finales:
        return {
            'valido': False,
            'mensaje': (
                'La accion esta en estado "' + accion.get_status_display()
                + '". No se pueden agregar compromisos a una accion finalizada.'
            ),
        }
    return {'valido': True, 'mensaje': 'Accion receptiva a compromisos.'}


def validar_compromiso_fecha(fecha_inicio, fecha_fin, accion_due_date=None):
    errores = []
    if fecha_inicio is None:
        errores.append('La fecha de inicio es requerida.')
    if fecha_fin is None:
        errores.append('La fecha limite es requerida.')
    if fecha_inicio and fecha_fin:
        if fecha_inicio > fecha_fin:
            errores.append('La fecha de inicio debe ser anterior a la fecha limite.')
    if fecha_fin and accion_due_date:
        if fecha_fin > accion_due_date:
            errores.append(
                'La fecha limite del compromiso (' + str(fecha_fin)
                + ') excede la fecha limite de la accion (' + str(accion_due_date) + ').'
            )
    return {'valido': len(errores) == 0, 'errores': errores}


def validar_descripcion_requerida(descripcion, minimo=10):
    if not descripcion or not descripcion.strip():
        return {'valido': False, 'mensaje': 'La descripcion es requerida.'}
    if len(descripcion.strip()) < minimo:
        return {
            'valido': False,
            'mensaje': 'La descripcion debe tener al menos ' + str(minimo) + ' caracteres.',
        }
    return {'valido': True, 'mensaje': 'Descripcion valida.'}
