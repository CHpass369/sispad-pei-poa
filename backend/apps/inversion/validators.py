from decimal import Decimal

ETAPAS_VALIDAS = ['preinversion', 'inversion', 'cierre', 'operacion']
TRANSICIONES_ETAPA = {
    'preinversion': ['inversion'],
    'inversion': ['cierre'],
    'cierre': ['operacion'],
}


def validar_proyecto_estado(proyecto, nuevo_estado):
    permitidos = TRANSICIONES_ETAPA.get(proyecto.etapa, [])
    if nuevo_estado not in permitidos:
        return {
            'valido': False,
            'mensaje': (
                'No se puede cambiar de "' + proyecto.get_etapa_display()
                + '" a "' + nuevo_estado + '". Estados validos: ' + str(permitidos)
            ),
        }
    return {'valido': True, 'mensaje': 'Transicion de estado valida.'}


def validar_avance_fisico_0_100(avance):
    if avance < Decimal('0') or avance > Decimal('100'):
        return {
            'valido': False,
            'mensaje': 'El avance fisico (' + str(avance) + '%) debe estar entre 0 y 100.',
        }
    return {'valido': True, 'mensaje': 'Avance fisico valido.'}


def validar_monto_inversion(monto):
    if monto is None:
        return {'valido': False, 'mensaje': 'El monto de inversion es requerido.'}
    if monto <= Decimal('0'):
        return {'valido': False, 'mensaje': 'El monto de inversion debe ser mayor a cero.'}
    return {'valido': True, 'mensaje': 'Monto de inversion valido.'}
