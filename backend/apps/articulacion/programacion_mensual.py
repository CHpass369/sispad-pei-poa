"""Forma canónica de la programación mensual, normalizada en el borde de la API.

El campo `programacion_mensual` es un `jsonb` y hoy le escriben tres clientes con
tres formas incompatibles:

- el importador de POAUs, con los meses en **minúscula**
  (``importar_poaus.py`` → ``{'enero': 230.0, …}``);
- el asistente POAU del frontend, con los meses en **MAYÚSCULA**
  (``poau-matriz.model.ts`` → ``{'ENERO': 230, …}``);
- el formulario de matriz M3, con un **array de doce posiciones**
  (``articulacion-form-m3.component.ts`` → ``Array(12).fill(null)``).

Los tres postean a los mismos endpoints. Mientras el mes sea texto libre dentro
de un blob, cada cliente elige su convención y nadie se entera: una consulta que
agrupe por ``'junio'`` ignora en silencio lo que se guardó como ``'JUNIO'`` y
devuelve un total más bajo, sin error.

Este módulo pone una sola puerta. Acepta las tres formas —para no romper a
ningún cliente que ya está escribiendo— y guarda siempre la misma: un objeto con
los doce meses en minúscula y sólo las claves que traen valor. Lo que no encaja
se rechaza con un mensaje claro en vez de entrar mudo.

Es la mitad barata del arreglo. La definitiva es llevar la programación a una
tabla con `mes` como entero 1–12 y `UNIQUE(entidad, mes)`, donde un mes mal
escrito directamente no tiene dónde entrar; esta normalización deja los datos
listos para esa migración y, mientras tanto, corta la corrupción.
"""
from decimal import Decimal, InvalidOperation

from rest_framework import serializers

MESES = (
    'enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
    'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre',
)


def _monto(valor, referencia):
    """Devuelve el valor como número, o None si viene vacío."""
    if valor is None or valor == '':
        return None
    if isinstance(valor, bool):
        raise serializers.ValidationError(
            f'El valor de «{referencia}» debe ser un número, no un booleano.'
        )
    if isinstance(valor, (int, float, Decimal)):
        return valor
    try:
        return float(Decimal(str(valor).strip()))
    except (InvalidOperation, ValueError, TypeError):
        raise serializers.ValidationError(
            f'El valor de «{referencia}» debe ser un número; llegó {valor!r}.'
        ) from None


def normalizar(valor):
    """Lleva cualquiera de las tres formas aceptadas a la forma canónica."""
    if valor is None or valor == '':
        return None

    if isinstance(valor, list):
        if len(valor) != len(MESES):
            raise serializers.ValidationError(
                f'La programación mensual como lista debe traer exactamente '
                f'{len(MESES)} posiciones (enero a diciembre); llegaron '
                f'{len(valor)}.'
            )
        pares = zip(MESES, valor)
    elif isinstance(valor, dict):
        pares = []
        for clave, monto in valor.items():
            mes = str(clave).strip().lower()
            if mes not in MESES:
                raise serializers.ValidationError(
                    f'«{clave}» no es un mes válido. Se esperaba uno de: '
                    f'{", ".join(MESES)}.'
                )
            pares.append((mes, monto))
    else:
        raise serializers.ValidationError(
            'La programación mensual debe ser un objeto con los meses por '
            'clave o una lista de doce posiciones.'
        )

    canonica = {}
    for mes, bruto in pares:
        monto = _monto(bruto, mes)
        if monto is None:
            continue
        if mes in canonica:
            raise serializers.ValidationError(
                f'El mes «{mes}» llegó dos veces con distinta grafía.'
            )
        canonica[mes] = monto
    return canonica or None


class ProgramacionMensualMixin:
    """Normaliza `programacion_mensual` en cualquier serializer que la exponga."""

    def validate_programacion_mensual(self, valor):
        return normalizar(valor)


class EjecucionMensualMixin:
    """Igual que el anterior, para el campo `ejecucion_mensual` de seguimiento."""

    def validate_ejecucion_mensual(self, valor):
        return normalizar(valor)
