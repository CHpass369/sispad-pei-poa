"""Semáforo de avance compartido por seguimiento, poau y reportes.

Única fuente de verdad para los umbrales:
- Verde: >= 80%
- Amarillo: 50% - 79%
- Rojo: < 50%
"""
from decimal import Decimal, InvalidOperation

UMBRAL_VERDE = Decimal('80')
UMBRAL_AMARILLO = Decimal('50')


def _decimal(value):
    if value is None:
        return Decimal('0')
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return Decimal('0')


def determinar_semaforo(percentage):
    """Retorna el color del semáforo basado en el porcentaje de avance."""
    p = _decimal(percentage)
    if p >= UMBRAL_VERDE:
        return 'verde'
    elif p >= UMBRAL_AMARILLO:
        return 'amarillo'
    return 'rojo'
