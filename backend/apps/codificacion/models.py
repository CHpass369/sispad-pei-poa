"""Catálogos oficiales versionados de codificación PAD-PEI-POA-POAU.

Todos los códigos oficiales (PGDESA, PDESA, sectores, CGEO, PAD) viven en
esta app, versionados por plan y gestión. El código nunca es PK y nunca lo
escribe el frontend.
"""
import uuid

from django.core.validators import RegexValidator
from django.db import models
from django.db.models import Q

from apps.core.models import TimeStampedModel


class VersionCatalogoPlan(TimeStampedModel):
    """Versión de los catálogos oficiales de un plan para una gestión.

    Una versión agrupa todos los catálogos (ejes, componentes, sectores,
    resultados, lineamientos PAD) aprobados por una norma. Solo puede
    existir una versión vigente por plan.
    """

    ESTADO_BORRADOR = 'borrador'
    ESTADO_VIGENTE = 'vigente'
    ESTADO_CERRADO = 'cerrado'
    ESTADO_CHOICES = [
        (ESTADO_BORRADOR, 'Borrador'),
        (ESTADO_VIGENTE, 'Vigente'),
        (ESTADO_CERRADO, 'Cerrado'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    plan = models.ForeignKey(
        'planificacion.Plan',
        on_delete=models.CASCADE,
        related_name='versiones_catalogo',
        verbose_name='Plan',
    )
    gestion = models.PositiveIntegerField(verbose_name='Gestión')
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default=ESTADO_BORRADOR,
        verbose_name='Estado',
    )
    norma_aprobacion = models.CharField(
        max_length=300,
        blank=True,
        verbose_name='Norma de aprobación',
    )

    class Meta:
        verbose_name = 'Versión de catálogo de plan'
        verbose_name_plural = 'Versiones de catálogo de planes'
        ordering = ['plan', 'gestion']
        constraints = [
            models.UniqueConstraint(
                fields=['plan', 'gestion'],
                name='uniq_version_catalogo_plan_gestion',
            ),
            models.UniqueConstraint(
                fields=['plan'],
                condition=Q(estado='vigente'),
                name='uniq_version_catalogo_vigente_por_plan',
            ),
        ]
        indexes = [
            models.Index(fields=['estado']),
            models.Index(fields=['gestion']),
        ]

    def __str__(self):
        return f'{self.plan.codigo} — {self.gestion} ({self.get_estado_display()})'
