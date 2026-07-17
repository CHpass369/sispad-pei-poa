from decimal import Decimal


def validar_meta_tipo_indicador(indicador):
    if indicador.tipo_comportamiento in ('acumulable', 'no_acumulable', 'promedio'):
        if indicador.meta_anual is None or indicador.meta_anual <= 0:
            return {
                'valido': False,
                'mensaje': 'El indicador de tipo "' + indicador.get_tipo_comportamiento_display() + '" requiere una meta anual positiva.',
            }
    return {'valido': True, 'mensaje': 'Meta valida para el tipo de indicador.'}


def validar_linea_base(indicador):
    if indicador.linea_base is None:
        return {'valido': False, 'mensaje': 'El indicador no tiene linea base definida.'}
    if indicador.linea_base < Decimal('0'):
        return {'valido': False, 'mensaje': 'La linea base no puede ser negativa.'}
    if not indicador.anio_linea_base:
        return {'valido': False, 'mensaje': 'Falta el anio de la linea base.'}
    return {'valido': True, 'mensaje': 'Linea base valida.'}


def validar_meta_programada_positiva(meta):
    if meta.meta_anual < Decimal('0'):
        return {'valido': False, 'mensaje': 'La meta anual programada no puede ser negativa.'}
    campos_trim = [meta.trimestre1, meta.trimestre2, meta.trimestre3, meta.trimestre4]
    valores_trim = [v for v in campos_trim if v is not None]
    if valores_trim:
        negativos = [v for v in valores_trim if v < Decimal('0')]
        if negativos:
            return {'valido': False, 'mensaje': 'Los valores trimestrales no pueden ser negativos.'}
        suma = sum(valores_trim)
        if meta.meta_anual and suma != meta.meta_anual:
            return {
                'valido': False,
                'mensaje': 'La suma de trimestres (' + str(suma) + ') no coincide con la meta anual (' + str(meta.meta_anual) + ').',
            }
    return {'valido': True, 'mensaje': 'Meta programada valida.'}
