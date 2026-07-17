def validar_geometria_valida(geometria):
    if geometria is None:
        return {'valido': False, 'mensaje': 'La geometria es requerida.'}
    if not geometria.valid:
        return {'valido': False, 'mensaje': 'La geometria no es geometricamente valida.'}
    if geometria.empty:
        return {'valido': False, 'mensaje': 'La geometria esta vacia.'}
    return {'valido': True, 'mensaje': 'Geometria valida.'}


def validar_crs(geometria, srid_esperado=4326):
    if geometria is None:
        return {'valido': False, 'mensaje': 'La geometria es requerida.'}
    if geometria.srid != srid_esperado:
        return {
            'valido': False,
            'mensaje': (
                'El CRS de la geometria (EPSG:' + str(geometria.srid)
                + ') no coincide con el esperado (EPSG:' + str(srid_esperado) + ').'
            ),
        }
    return {'valido': True, 'mensaje': 'CRS valido.'}


def validar_area_positiva(geometria):
    if geometria is None:
        return {'valido': False, 'mensaje': 'La geometria es requerida.'}
    if geometria.area <= 0:
        return {'valido': False, 'mensaje': 'El area de la geometria debe ser mayor a cero.'}
    return {'valido': True, 'mensaje': 'Area valida.'}
