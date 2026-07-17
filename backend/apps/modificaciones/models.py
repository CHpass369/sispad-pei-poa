import uuid
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from apps.core.models import TimeStampedModel


class SolicitudModificacion(TimeStampedModel):
    TIPO_CHOICES = [
        ('meta', 'Modificación de Meta'),
        ('operacion', 'Modificación de Operación'),
        ('reprogramacion', 'Reprogramación'),
        ('responsable', 'Cambio de Responsable'),
        ('inscripcion', 'Inscripción'),
        ('eliminacion', 'Eliminación'),
        ('incremento', 'Incremento Presupuestario'),
        ('reduccion', 'Reducción Presupuestaria'),
        ('traspaso', 'Traspaso Presupuestario'),
        ('fuente', 'Cambio de Fuente de Financiamiento'),
        ('organismo', 'Cambio de Organismo Financiador'),
        ('categoria', 'Cambio de Categoría'),
        ('reformulacion', 'Reformulación'),
    ]

    ESTADO_CHOICES = [
        ('borrador', 'Borrador'),
        ('en_revision', 'En Revisión'),
        ('aprobada', 'Aprobada'),
        ('rechazada', 'Rechazada'),
        ('cumplida', 'Cumplida'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, verbose_name='Tipo de modificación')
    gestion_fiscal = models.PositiveIntegerField(verbose_name='Gestión fiscal')
    entidad_afectada_tipo = models.CharField(
        max_length=100,
        verbose_name='Tipo de entidad afectada',
        help_text='Nombre del modelo ContentType de la entidad afectada',
    )
    entidad_afectada_id = models.UUIDField(verbose_name='ID de entidad afectada')
    poau = models.ForeignKey(
        'poau.POAU', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='solicitudes_modificacion',
        verbose_name='POAU',
    )
    motivo = models.TextField(verbose_name='Motivo de la modificación')
    informe_tecnico = models.TextField(blank=True, verbose_name='Informe técnico')
    documento_legal = models.TextField(blank=True, verbose_name='Documento legal / respaldo normativo')
    solicitado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='solicitudes_modificacion',
        verbose_name='Solicitado por',
    )
    estado = models.CharField(max_length=15, choices=ESTADO_CHOICES, default='borrador')
    fecha_efectiva = models.DateField(null=True, blank=True, verbose_name='Fecha efectiva')
    observaciones = models.TextField(blank=True, verbose_name='Observaciones')
    version = models.PositiveIntegerField(default=1, verbose_name='Versión')

    class Meta:
        verbose_name = 'Solicitud de modificación'
        verbose_name_plural = 'Solicitudes de modificación'
        ordering = ['-created_at', 'gestion_fiscal']
        indexes = [
            models.Index(fields=['gestion_fiscal', 'estado']),
            models.Index(fields=['entidad_afectada_tipo', 'entidad_afectada_id']),
            models.Index(fields=['tipo', 'estado']),
        ]

    def __str__(self):
        return f'{self.get_tipo_display()} — {self.entidad_afectada_tipo} ({self.get_estado_display()})'


class CambioModificacion(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    solicitud = models.ForeignKey(
        SolicitudModificacion, on_delete=models.CASCADE,
        related_name='cambios',
    )
    campo = models.CharField(max_length=200, verbose_name='Campo')
    valor_anterior = models.TextField(blank=True, verbose_name='Valor anterior')
    valor_propuesto = models.TextField(blank=True, verbose_name='Valor propuesto')
    valor_aprobado = models.TextField(null=True, blank=True, verbose_name='Valor aprobado')

    class Meta:
        verbose_name = 'Cambio de modificación'
        verbose_name_plural = 'Cambios de modificación'
        ordering = ['solicitud', 'campo']

    def __str__(self):
        return f'{self.campo}: {self.valor_anterior} → {self.valor_propuesto}'


class ImpactoModificacion(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    solicitud = models.OneToOneField(
        SolicitudModificacion, on_delete=models.CASCADE,
        related_name='impacto',
    )
    impacto_fisico = models.TextField(blank=True, verbose_name='Impacto físico')
    impacto_financiero = models.DecimalField(
        max_digits=20, decimal_places=2, default=0,
        validators=[MinValueValidator(0)],
        verbose_name='Impacto financiero',
    )
    impacto_estrategico = models.TextField(blank=True, verbose_name='Impacto estratégico')
    documento_aprobacion = models.TextField(blank=True, verbose_name='Documento de aprobación')

    class Meta:
        verbose_name = 'Impacto de modificación'
        verbose_name_plural = 'Impactos de modificación'

    def __str__(self):
        return f'Impacto: {self.solicitud.get_tipo_display()} — Bs. {self.impacto_financiero}'
