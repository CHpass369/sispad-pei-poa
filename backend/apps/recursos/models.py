import uuid
from django.db import models
from django.core.validators import MinValueValidator
from apps.core.models import TimeStampedModel
from apps.catalogos.models import RubroRecurso, FuenteFinanciamiento, OrganismoFinanciador


class EstimacionRecurso(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    gestion = models.PositiveIntegerField()
    rubro = models.ForeignKey(RubroRecurso, on_delete=models.PROTECT, related_name='estimaciones')
    fuente = models.ForeignKey(FuenteFinanciamiento, on_delete=models.PROTECT, related_name='estimaciones')
    organismo = models.ForeignKey(OrganismoFinanciador, on_delete=models.PROTECT, null=True, blank=True, related_name='estimaciones')
    monto_estimado = models.DecimalField(max_digits=20, decimal_places=2, validators=[MinValueValidator(0)])
    memoria_calculo = models.TextField(blank=True)
    activo = models.BooleanField(default=True)
    version = models.PositiveIntegerField(default=1)

    class Meta:
        verbose_name = 'Estimación de recurso'
        verbose_name_plural = 'Estimaciones de recursos'
        ordering = ['gestion', 'rubro__codigo']
        indexes = [
            models.Index(fields=['gestion', 'fuente']),
        ]

    def __str__(self):
        return f'{self.rubro.denominacion} - {self.gestion}: Bs {self.monto_estimado}'


class EstimacionPlurianual(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    estimacion_origen = models.ForeignKey(
        EstimacionRecurso, on_delete=models.CASCADE,
        related_name='proyecciones'
    )
    anio = models.PositiveIntegerField()
    monto_proyectado = models.DecimalField(max_digits=20, decimal_places=2, validators=[MinValueValidator(0)])

    class Meta:
        verbose_name = 'Estimación plurianual'
        verbose_name_plural = 'Estimaciones plurianuales'
        unique_together = [('estimacion_origen', 'anio')]
        ordering = ['estimacion_origen', 'anio']
