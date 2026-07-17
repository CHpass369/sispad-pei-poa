def validar_poau_borrador(poau):
    if poau is None:
        return {'valido': False, 'mensaje': 'El POAU no existe.'}
    if poau.estado != 'borrador':
        return {
            'valido': False,
            'mensaje': (
                'El POAU esta en estado "' + poau.get_estado_display()
                + '". Solo se pueden editar POAUs en borrador.'
            ),
        }
    return {'valido': True, 'mensaje': 'POAU en borrador, editable.'}


def validar_actividad_trimestre(actividad):
    trimestres = [actividad.meta_q1, actividad.meta_q2, actividad.meta_q3, actividad.meta_q4]
    valores = [v for v in trimestres if v is not None]
    if not valores:
        return {'valido': True, 'mensaje': 'Sin programacion trimestral.'}
    negativos = [v for v in valores if v < 0]
    if negativos:
        return {'valido': False, 'mensaje': 'Los valores trimestrales no pueden ser negativos.'}
    if actividad.meta_fisica_anual is not None:
        suma = sum(valores)
        if suma != actividad.meta_fisica_anual:
            return {
                'valido': False,
                'mensaje': (
                    'La suma de trimestres (' + str(suma)
                    + ') no coincide con la meta anual ('
                    + str(actividad.meta_fisica_anual) + ').'
                ),
            }
    return {'valido': True, 'mensaje': 'Programacion trimestral valida.'}


def validar_ejecucion_positiva(programado, ejecutado):
    if programado < 0:
        return {'valido': False, 'mensaje': 'El programado no puede ser negativo.'}
    if ejecutado < 0:
        return {'valido': False, 'mensaje': 'Lo ejecutado no puede ser negativo.'}
    return {'valido': True, 'mensaje': 'Valores de ejecucion validos.'}


def validar_tecnico_reporte(actividad_id):
    from apps.poau.models import POAUActividad
    try:
        actividad = POAUActividad.objects.get(id=actividad_id)
    except POAUActividad.DoesNotExist:
        return {'valido': False, 'mensaje': 'Actividad no encontrada.'}
    errores = []
    if not actividad.codigo:
        errores.append('Falta codigo de actividad.')
    if not actividad.nombre:
        errores.append('Falta nombre de actividad.')
    if actividad.meta_fisica_anual is None:
        errores.append('Falta meta fisica anual.')
    return {'valido': len(errores) == 0, 'errores': errores}
