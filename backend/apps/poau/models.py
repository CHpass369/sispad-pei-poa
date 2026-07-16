from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from apps.core.models import TimeStampedModel


class POAU(models.Model):
    """Plan Operativo Anual por Unidad"""

    ESTADO_CHOICES = [
        ('borrador', 'Borrador'),
        ('enviado', 'Enviado'),
        ('aprobado', 'Aprobado'),
        ('rechazado', 'Rechazado'),
    ]

    unidad = models.ForeignKey(
        'organizacion.UnidadOrganizacional', on_delete=models.PROTECT,
        related_name='poaus',
    )
    producto_territorial = models.ForeignKey(
        'pad.ProductoTerritorial', on_delete=models.PROTECT,
        null=True, blank=True, related_name='poaus',
    )
    gestion = models.PositiveIntegerField()
    codigo = models.CharField(max_length=50, unique=True)
    nombre = models.TextField()
    descripcion = models.TextField(blank=True)
    estado = models.CharField(
        max_length=20, choices=ESTADO_CHOICES, default='borrador',
    )
    responsable = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='poaus_responsable',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'POAU'
        verbose_name_plural = 'POAUs'
        ordering = ['gestion', 'codigo']

    def __str__(self):
        return f'[{self.codigo}] {self.nombre[:80]}'


class POAUActividad(models.Model):
    """Actividad del POAU — cada actividad tiene programación y ejecución"""

    poau = models.ForeignKey(
        POAU, on_delete=models.CASCADE, related_name='actividades',
    )
    codigo = models.CharField(max_length=50)
    nombre = models.TextField()
    objeto_gasto = models.ForeignKey(
        'catalogos.ObjetoGasto', on_delete=models.PROTECT,
        null=True, blank=True, related_name='+',
    )
    meta_fisica_anual = models.DecimalField(
        max_digits=20, decimal_places=4, null=True, blank=True,
    )
    presupuesto_anual = models.DecimalField(
        max_digits=20, decimal_places=2, null=True, blank=True,
    )
    meta_q1 = models.DecimalField(
        max_digits=20, decimal_places=4, null=True, blank=True,
        verbose_name='Meta Q1',
    )
    meta_q2 = models.DecimalField(
        max_digits=20, decimal_places=4, null=True, blank=True,
        verbose_name='Meta Q2',
    )
    meta_q3 = models.DecimalField(
        max_digits=20, decimal_places=4, null=True, blank=True,
        verbose_name='Meta Q3',
    )
    meta_q4 = models.DecimalField(
        max_digits=20, decimal_places=4, null=True, blank=True,
        verbose_name='Meta Q4',
    )
    accion_corto_plazo = models.ForeignKey(
        'planificacion.AccionCortoPlazo', on_delete=models.PROTECT,
        null=True, blank=True, related_name='actividades_poau',
        verbose_name='Acción de Corto Plazo',
    )

    class Meta:
        verbose_name = 'Actividad POAU'
        verbose_name_plural = 'Actividades POAU'
        unique_together = [('poau', 'codigo')]
        ordering = ['poau', 'codigo']

    def __str__(self):
        return f'[{self.codigo}] {self.nombre[:80]}'

    def clean(self):
        trimestres = [self.meta_q1, self.meta_q2, self.meta_q3, self.meta_q4]
        if all(t is not None for t in trimestres):
            suma = sum(trimestres)
            if self.meta_fisica_anual is not None and suma != self.meta_fisica_anual:
                raise ValidationError(
                    f'La suma de trimestres ({suma}) debe coincidir con '
                    f'la meta anual ({self.meta_fisica_anual})'
                )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class EjecucionFisica(models.Model):
    """Ejecución física mensual/trimestral/semestral/anual"""

    TIPO_PERIODO_CHOICES = [
        ('mensual', 'Mensual'),
        ('trimestral', 'Trimestral'),
        ('semestral', 'Semestral'),
        ('anual', 'Anual'),
    ]

    actividad = models.ForeignKey(
        POAUActividad, on_delete=models.CASCADE,
        related_name='ejecucion_fisica',
    )
    periodo = models.CharField(
        max_length=20,
        help_text='Formato: 2026-01, 2026-Q1, 2026-S1, 2026',
    )
    tipo_periodo = models.CharField(
        max_length=10, choices=TIPO_PERIODO_CHOICES,
    )
    programado = models.DecimalField(
        max_digits=20, decimal_places=4, default=0,
    )
    ejecutado = models.DecimalField(
        max_digits=20, decimal_places=4, default=0,
    )
    observaciones = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Ejecución física'
        verbose_name_plural = 'Ejecuciones físicas'
        unique_together = [('actividad', 'periodo')]
        ordering = ['periodo']

    def __str__(self):
        return f'{self.actividad.codigo} — {self.periodo}'


class EjecucionFinanciera(models.Model):
    """Ejecución financiera — seguimiento presupuestario"""

    TIPO_PERIODO_CHOICES = [
        ('mensual', 'Mensual'),
        ('trimestral', 'Trimestral'),
        ('semestral', 'Semestral'),
        ('anual', 'Anual'),
    ]

    actividad = models.ForeignKey(
        POAUActividad, on_delete=models.CASCADE,
        related_name='ejecucion_financiera',
    )
    periodo = models.CharField(
        max_length=20,
        help_text='Formato: 2026-01, 2026-Q1, 2026-S1, 2026',
    )
    tipo_periodo = models.CharField(
        max_length=10, choices=TIPO_PERIODO_CHOICES,
    )
    programado = models.DecimalField(
        max_digits=20, decimal_places=2, default=0,
    )
    ejecutado = models.DecimalField(
        max_digits=20, decimal_places=2, default=0,
    )
    observaciones = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Ejecución financiera'
        verbose_name_plural = 'Ejecuciones financieras'
        unique_together = [('actividad', 'periodo')]
        ordering = ['periodo']

    def __str__(self):
        return f'{self.actividad.codigo} — {self.periodo}'
