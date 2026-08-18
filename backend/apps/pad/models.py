from django.db import models

from apps.core.models import TimeStampedModel


class SectorPAD(TimeStampedModel):
    """Catálogo canónico de sectores del PAD (20 sectores municipales).

    Único modelo sobreviviente de la app tras el retiro de la jerarquía PAD
    legacy (política → lineamiento → resultado → producto → programación),
    reemplazada por la cadena de `apps.articulacion` que alimenta Matriz PAD.

    Pendiente: reubicar este catálogo en su dominio definitivo. Requiere el
    mapeo oficial sector → componente PDESA, que hoy no existe en el sistema.
    """

    codigo = models.CharField(max_length=10, unique=True)
    nombre = models.CharField(max_length=200)

    class Meta:
        verbose_name = 'Sector PAD'
        verbose_name_plural = 'Sectores PAD'
        ordering = ['codigo']

    def __str__(self):
        return f'[{self.codigo}] {self.nombre}'
