from decimal import Decimal


def validar_fuente_financiamiento(fuente_id):
    if fuente_id is None:
        return {'valido': False, 'mensaje': 'La fuente de financiamiento es requerida.'}
    from apps.catalogos.models import FuenteFinanciamiento
    if not FuenteFinanciamiento.objects.filter(id=fuente_id).exists():
        return {'valido': False, 'mensaje': 'La fuente de financiamiento no existe.'}
    return {'valido': True, 'mensaje': 'Fuente de financiamiento valida.'}


def validar_monto_positivo(monto, campo='monto'):
    if monto is None:
        return {'valido': False, 'mensaje': 'El campo "' + campo + '" es requerido.'}
    if monto < Decimal('0'):
        return {'valido': False, 'mensaje': 'El campo "' + campo + '" no puede ser negativo.'}
    return {'valido': True, 'mensaje': campo + ' valido.'}


def validar_linea_igual_total_presupuesto(lineas, total_presupuesto):
    suma = sum(Decimal(str(l.get('monto', 0))) for l in lineas)
    total = Decimal(str(total_presupuesto))
    if suma != total:
        return {
            'valido': False,
            'mensaje': 'La suma de lineas (Bs ' + str(suma) + ') no coincide con el total (Bs ' + str(total) + ').',
            'diferencia': total - suma,
        }
    return {'valido': True, 'mensaje': 'Lineas coinciden con el total.', 'diferencia': Decimal('0')}
