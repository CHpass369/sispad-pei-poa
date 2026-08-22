"""Ayudas de test para el candado de gestión fiscal (ADR-007).

Los módulos de SIS-POA no responden sin gestión habilitada, así que sus tests
tienen que declarar cuál es. Antes el año viajaba suelto en cada petición y no
hacía falta decirlo; ahora es una precondición del dominio, no un parámetro.
"""
from .models import GestionFiscal


def habilitar_gestion_para_tests(anio, **extra):
    """Deja el candado en `anio` y lo quita de cualquier otra gestión.

    Se libera primero porque el índice único parcial `unica_gestion_habilitada`
    admite una sola fila con `activa=True`.
    """
    GestionFiscal.objects.exclude(anio=anio).update(activa=False)
    gestion, _ = GestionFiscal.objects.update_or_create(
        anio=anio,
        defaults={'estado': 'HABILITADA', 'activa': True, **extra},
    )
    return gestion
