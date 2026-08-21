"""Reglas de la directriz de formulación sobre la categoría programática."""
from django.core.exceptions import ValidationError

from .categoria import partes_categoria
from .models import RangoProgramaDirectriz

# La directriz lo dice expresamente: «Los programas del 10 al 96 no podrán ser
# apropiados ni utilizados».
PROHIBIDO_DESDE, PROHIBIDO_HASTA = 10, 96


def rango_de(programa, gestion,
             nivel=RangoProgramaDirectriz.NIVEL_MUNICIPAL):
    """El rango de la directriz al que pertenece un programa.

    Cuando la directriz singulariza un programa dentro de un rango —el 251
    dentro de 250-259— gana el más específico: es el que trae su propia
    finalidad y su propio sector.
    """
    try:
        numero = int(str(programa).strip())
    except (TypeError, ValueError):
        return None
    candidatos = [r for r in RangoProgramaDirectriz.objects
                  .filter(gestion=int(gestion), nivel_entidad=nivel)
                  if r.contiene(numero)]
    if not candidatos:
        return None
    return min(candidatos, key=lambda r: r.hasta - r.desde)


def programa_prohibido(programa):
    """¿Cae en la franja que la directriz reserva y prohíbe usar?"""
    try:
        numero = int(str(programa).strip())
    except (TypeError, ValueError):
        return False
    return PROHIBIDO_DESDE <= numero <= PROHIBIDO_HASTA


def validar_categoria(codigo, gestion,
                      nivel=RangoProgramaDirectriz.NIVEL_MUNICIPAL):
    """Verifica un código contra la directriz. Devuelve el rango que aplica.

    Levanta ValidationError con el motivo: un código mal formado que entra en
    silencio reaparece recién en el reporte al Ministerio, cuando ya no hay
    margen para corregirlo.
    """
    partes = partes_categoria(codigo)
    if not partes.valida:
        raise ValidationError(
            f'La categoría «{codigo}» no tiene los tres segmentos que exige la '
            'directriz: programa, proyecto (código SISIN) y actividad.')
    if not partes.programa.isdigit():
        raise ValidationError(
            f'El programa «{partes.programa}» debe ser numérico.')
    if programa_prohibido(partes.programa):
        raise ValidationError(
            f'El programa {int(partes.programa)} no se puede usar: la '
            f'directriz reserva del {PROHIBIDO_DESDE} al {PROHIBIDO_HASTA} y '
            'dispone que no sean apropiados ni utilizados.')
    rango = rango_de(partes.programa, gestion, nivel)
    if rango is None:
        raise ValidationError(
            f'El programa {int(partes.programa)} no corresponde a ningún rango '
            f'de la directriz {gestion}. Verifique el código o cargue la '
            'directriz con «sembrar_directriz_programas».')
    return rango
