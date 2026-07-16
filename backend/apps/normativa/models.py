import uuid
from django.db import models
from django.core.exceptions import ValidationError
from apps.core.models import TimeStampedModel, ActivableModel, VigenciaModel


class VersionNormativa(TimeStampedModel, ActivableModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    titulo = models.CharField(max_length=500)
    tipo = models.CharField(max_length=50, choices=[
        ('ley', 'Ley'),
        ('decreto', 'Decreto Supremo'),
        ('resolucion', 'Resolución Ministerial'),
        ('directriz', 'Directriz de Formulación'),
        ('norma', 'Norma Básica'),
        ('ordenanza', 'Ordenanza Municipal'),
        ('otro', 'Otro'),
    ])
    numero = models.CharField(max_length=100, blank=True)
    fecha_emision = models.DateField(null=True, blank=True)
    gestion = models.PositiveIntegerField()
    archivo = models.FileField(upload_to='normativa/', null=True, blank=True)
    resumen = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Versión normativa'
        verbose_name_plural = 'Versiones normativas'
        ordering = ['-gestion', '-fecha_emision']
        indexes = [
            models.Index(fields=['gestion', 'tipo']),
        ]

    def __str__(self):
        return f'{self.get_tipo_display()} {self.numero} - {self.titulo}'


class ReglaPresupuestariaLegal(TimeStampedModel, ActivableModel):
    class Tipo(models.TextChoices):
        LIMITE = 'limite', 'Límite'
        MINIMO = 'minimo', 'Mínimo'
        ADVERTENCIA = 'advertencia', 'Advertencia'
        PROHIBICION = 'prohibicion', 'Prohibición'
        CONSISTENCIA = 'consistencia', 'Consistencia'
        DOCUMENTACION = 'documentacion', 'Documentación'

    class Severidad(models.TextChoices):
        INFORMATIVA = 'informativa', 'Informativa'
        ADVERTENCIA = 'advertencia', 'Advertencia'
        BLOQUEANTE = 'bloqueante', 'Bloqueante'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    codigo = models.CharField(max_length=50, unique=True)
    nombre = models.CharField(max_length=300)
    descripcion = models.TextField()
    tipo = models.CharField(max_length=20, choices=Tipo)
    severidad = models.CharField(max_length=20, choices=Severidad, default=Severidad.BLOQUEANTE)
    formula = models.TextField(
        blank=True,
        help_text='Expresión segura para evaluación (implementada como método, no eval)'
    )
    parametros = models.JSONField(
        null=True, blank=True,
        help_text='Parámetros versionados en JSON: {"porcentaje": 0.10, "fuentes_permitidas": [...]}'
    )
    condicion_aplicabilidad = models.TextField(
        blank=True,
        help_text='Descripción de cuándo se aplica esta regla'
    )
    gestion_desde = models.PositiveIntegerField()
    gestion_hasta = models.PositiveIntegerField(null=True, blank=True)
    fuente_normativa = models.CharField(max_length=500, blank=True)
    mensaje = models.TextField(
        help_text='Mensaje comprensible para el usuario cuando la regla se incumple'
    )
    orden = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = 'Regla presupuestaria legal'
        verbose_name_plural = 'Reglas presupuestarias legales'
        ordering = ['gestion_desde', 'orden']
        indexes = [
            models.Index(fields=['tipo', 'severidad']),
        ]

    def __str__(self):
        return f'[{self.codigo}] {self.nombre}'

    def clean(self):
        if self.gestion_hasta and self.gestion_hasta < self.gestion_desde:
            raise ValidationError('La gestión hasta debe ser posterior a la gestión desde')
        # No usamos eval. La estrategia de cálculo está documentada en formula
        # y se implementa como método tipado en los servicios de dominio.

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
