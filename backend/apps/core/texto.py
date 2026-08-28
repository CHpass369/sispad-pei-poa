"""Normalización de texto para búsquedas y claves de unicidad.

Los nombres llegan escritos de mil formas —`ADQ.` y `Adquisición`, `O.T.B.` y
`OTB`, con tilde y sin tilde—. Comparar contra una clave plana es lo único que
hace que el buscador y las claves de unicidad se comporten igual que la
intuición de quien carga el dato.
"""
import re

_TILDES = str.maketrans('ÁÉÍÓÚÜÑ', 'AEIOUUN')


def normalizar(texto):
    """Clave de búsqueda: sin tildes, sin puntuación y en mayúsculas."""
    plano = str(texto or '').upper().translate(_TILDES)
    return re.sub(r'\s+', ' ', re.sub(r'[^A-Z0-9 ]', ' ', plano)).strip()
