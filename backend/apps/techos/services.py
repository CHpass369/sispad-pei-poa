from decimal import Decimal
from django.db import transaction
from .models import MovimientoTecho


def obtener_saldo_disponible(techo):
    movimientos_aprobados = MovimientoTecho.objects.filter(
        techo=techo,
        approved_by__isnull=False
    )

    saldo = techo.monto_total
    for mov in movimientos_aprobados:
        if mov.movement_type in ('asignacion', 'incremento', 'transferencia', 'ajuste'):
            saldo += mov.amount
        elif mov.movement_type in ('reduccion', 'reserva', 'liberacion', 'reversion'):
            saldo -= mov.amount
    return saldo


def validar_movimiento(movimiento):
    errores = []

    if movimiento.amount <= 0:
        errores.append('El monto del movimiento debe ser mayor a cero.')

    if movimiento.movement_type == 'transferencia':
        if not movimiento.source_ceiling:
            errores.append('Para transferencias se requiere un techo origen.')
        if not movimiento.destination_ceiling:
            errores.append('Para transferencias se requiere un techo destino.')
        if (movimiento.source_ceiling and
                movimiento.source_ceiling.id == movimiento.destination_ceiling_id):
            errores.append('El techo origen y destino no pueden ser el mismo.')

    if movimiento.movement_type in ('incremento', 'asignacion', 'transferencia', 'ajuste'):
        if movimiento.source_ceiling:
            saldo_origen = obtener_saldo_disponible(movimiento.source_ceiling)
            if movimiento.amount > saldo_origen:
                errores.append(
                    f'El monto Bs {movimiento.amount} excede el saldo disponible '
                    f'del techo origen Bs {saldo_origen}.'
                )

    return errores


@transaction.atomic
def aplicar_movimiento(movimiento):
    errores = validar_movimiento(movimiento)
    if errores:
        raise ValueError('; '.join(errores))

    movimientos_existentes = MovimientoTecho.objects.filter(
        techo=movimiento.techo,
        approved_by__isnull=False
    ).exclude(pk=movimiento.pk)

    total_movimientos = sum(
        m.amount for m in movimientos_existentes
        if m.movement_type in ('reduccion', 'reserva', 'liberacion', 'reversion')
    )
    total_incrementos = sum(
        m.amount for m in movimientos_existentes
        if m.movement_type in ('asignacion', 'incremento', 'transferencia', 'ajuste')
    )

    nuevo_total = movimiento.techo.monto_total + total_incrementos - total_movimientos
    if movimiento.movement_type in ('reduccion', 'reserva', 'liberacion', 'reversion'):
        if movimiento.amount > nuevo_total:
            raise ValueError(
                f'El monto de reducción Bs {movimiento.amount} excede '
                f'el saldo disponible Bs {nuevo_total}.'
            )

    movimiento.save()
    return movimiento
