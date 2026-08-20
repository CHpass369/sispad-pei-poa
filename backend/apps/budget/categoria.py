"""Lectura del código de categoría programática.

El código tiene tres segmentos y el del medio cambia de naturaleza según el
tipo de gasto:

    000 0 001              →  programa 000, subprograma 0, actividad 001
    180 08620281200000 000 →  programa 180, proyecto SISIN, actividad 000

Es el mismo campo en la misma columna, así que hay que mirar el contenido para
saber qué se está leyendo. Un SISIN tiene 14 caracteres; un subprograma, uno.
"""
import re
from dataclasses import dataclass

LARGO_SISIN = 10  # A partir de acá el segmento del medio ya no es subprograma.


def normalizar(codigo):
    """El código llega con espaciado irregular según de dónde se cargó."""
    return re.sub(r'\s+', ' ', str(codigo or '')).strip().upper()


@dataclass(frozen=True)
class Categoria:
    codigo: str
    programa: str
    segmento: str
    actividad: str

    @property
    def es_proyecto(self):
        """Un proyecto de inversión: el segmento del medio es su SISIN."""
        return len(self.segmento) >= LARGO_SISIN

    @property
    def sisin(self):
        return self.segmento if self.es_proyecto else ''

    @property
    def subprograma(self):
        return '' if self.es_proyecto else self.segmento

    @property
    def valida(self):
        return bool(self.programa and self.segmento and self.actividad)


def partes_categoria(codigo):
    """Descompone el código. Devuelve una Categoria aunque venga incompleto."""
    limpio = normalizar(codigo)
    partes = limpio.split(' ')
    if len(partes) != 3:
        # No se inventan segmentos: se devuelve lo que hay y `valida` avisa.
        return Categoria(codigo=limpio, programa=partes[0] if partes else '',
                         segmento='', actividad='')
    return Categoria(codigo=limpio, programa=partes[0], segmento=partes[1],
                     actividad=partes[2])


def codigo_programa(codigo):
    """El programa al que pertenece la categoría, para agrupar el gasto."""
    return partes_categoria(codigo).programa
