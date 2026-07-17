from decimal import Decimal


def validar_recurso_disponible(fuente_id, gestion, monto):
    from apps.techos.models import TechoPresupuestario
    from apps.presupuesto.models import LineaPresupuestaria
    from django.db.models import Sum

    techo = TechoPresupuestario.objects.filter(
        fuente_id=fuente_id, gestion=gestion, activo=True
    ).aggregate(total=Sum('monto_total'))['total'] or Decimal('0')
    asignado = LineaPresupuestaria.objects.filter(
        fuente_id=fuente_id, gestion=gestion, activo=True
    ).aggregate(total=Sum('importe'))['total'] or Decimal('0')
    disponible = techo - asignado
    if monto > disponible:
        return {
            'valido': False,
            'mensaje': 'Monto (Bs ' + str(monto) + ') excede disponibilidad (Bs ' + str(disponible) + ').',
        }
    return {'valido': True, 'mensaje': 'Recurso disponible.'}


def validar_tipo_recurso(rubro):
    if rubro is None:
        return {'valido': False, 'mensaje': 'El rubro de recurso es requerido.'}
    return {'valido': True, 'mensaje': 'Tipo de recurso valido.'}


def validar_cantidad_positiva(monto):
    if monto is None:
        return {'valido': False, 'mensaje': 'El monto es requerido.'}
    if monto < Decimal('0'):
        return {'valido': False, 'mensaje': 'El monto no puede ser negativo.'}
    return {'valido': True, 'mensaje': 'Cantidad valida.'}
