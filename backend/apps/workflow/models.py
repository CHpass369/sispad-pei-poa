import uuid
from django.db import models
from django.conf import settings
from apps.core.models import TimeStampedModel


class EnvioFormulacion(TimeStampedModel):
    """Registro de envío de formulación por parte de una unidad"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    unidad = models.ForeignKey(
        'organizacion.UnidadOrganizacional', on_delete=models.PROTECT,
        related_name='envios_formulacion'
    )
    gestion = models.PositiveIntegerField()
    version = models.PositiveIntegerField()
    enviado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='envios_realizados'
    )
    fecha_envio = models.DateTimeField(auto_now_add=True)
    comentario = models.TextField(blank=True)
    estado_anterior = models.CharField(max_length=50)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Envío de formulación'
        verbose_name_plural = 'Envíos de formulación'
        ordering = ['-fecha_envio']

    def __str__(self):
        return f'Envío {self.unidad.nombre} - v{self.version} ({self.fecha_envio})'


class Revision(TimeStampedModel):
    """Proceso de revisión por un revisor designado"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    envio = models.ForeignKey(EnvioFormulacion, on_delete=models.CASCADE, related_name='revisiones')
    tipo_revision = models.CharField(max_length=50, choices=[
        ('planificacion', 'Planificación'),
        ('presupuesto', 'Presupuesto'),
        ('inversion', 'Proyectos e Inversión'),
        ('juridica', 'Jurídica'),
    ])
    revisor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='revisiones_asignadas'
    )
    estado = models.CharField(max_length=20, choices=[
        ('pendiente', 'Pendiente'),
        ('en_curso', 'En curso'),
        ('completada', 'Completada'),
        ('devuelta', 'Devuelta'),
    ], default='pendiente')
    resultado = models.CharField(max_length=20, choices=[
        ('aprobado', 'Aprobado'),
        ('observado', 'Observado'),
        ('rechazado', 'Rechazado'),
    ], null=True, blank=True)
    fecha_asignacion = models.DateTimeField(auto_now_add=True)
    fecha_completado = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Revisión'
        verbose_name_plural = 'Revisiones'
        ordering = ['-fecha_asignacion']

    def __str__(self):
        return f'Revisión {self.get_tipo_revision_display()} - {self.envio}'


class Observacion(TimeStampedModel):
    TIPO_CHOICES = [
        ('forma', 'Forma'),
        ('fondo', 'Fondo'),
        ('legal', 'Legal'),
        ('presupuestaria', 'Presupuestaria'),
        ('tecnica', 'Técnica'),
        ('documental', 'Documental'),
    ]
    SEVERIDAD_CHOICES = [
        ('leve', 'Leve'),
        ('moderada', 'Moderada'),
        ('grave', 'Grave'),
    ]
    ESTADO_CHOICES = [
        ('abierta', 'Abierta'),
        ('respondida', 'Respondida'),
        ('aceptada', 'Aceptada'),
        ('rechazada', 'Rechazada'),
        ('cerrada', 'Cerrada'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    codigo = models.CharField(max_length=50, unique=True)
    revision = models.ForeignKey(Revision, on_delete=models.CASCADE, null=True, blank=True, related_name='observaciones')
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    severidad = models.CharField(max_length=20, choices=SEVERIDAD_CHOICES, default='moderada')
    modulo = models.CharField(max_length=50, help_text='Módulo afectado (ej: indicadores, presupuesto)')
    registro_id = models.CharField(max_length=100, help_text='ID del registro afectado')
    texto = models.TextField()
    responsable_subsanacion = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='observaciones_asignadas'
    )
    fecha_limite = models.DateTimeField(null=True, blank=True)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='abierta')
    respuesta = models.TextField(blank=True)
    evidencia_subsanacion = models.TextField(blank=True)
    gestion = models.PositiveIntegerField()

    class Meta:
        verbose_name = 'Observación'
        verbose_name_plural = 'Observaciones'
        ordering = ['-created_at']

    def __str__(self):
        return f'[{self.codigo}] {self.get_tipo_display()} - {self.estado}'


class Aprobacion(TimeStampedModel):
    """Registro de aprobación con huella digital"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    gestion = models.PositiveIntegerField()
    tipo = models.CharField(max_length=50, choices=[
        ('unidad', 'Aprobación de unidad'),
        ('planificacion', 'Validación de Planificación'),
        ('presupuesto', 'Validación de Presupuesto'),
        ('consolidacion', 'Consolidación institucional'),
        ('control_social', 'Pronunciamiento Control Social'),
        ('mae', 'Aprobación MAE'),
        ('concejo', 'Aprobación Concejo Municipal'),
    ])
    aprobado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='aprobaciones'
    )
    estado = models.CharField(max_length=20, choices=[
        ('aprobado', 'Aprobado'),
        ('observado', 'Observado'),
        ('rechazado', 'Rechazado'),
    ])
    comentario = models.TextField(blank=True)
    version = models.PositiveIntegerField()
    huella_documento = models.CharField(max_length=64, blank=True, help_text='SHA-256 del documento aprobado')
    documento = models.ForeignKey(
        'documentos.DocumentoAdjunto', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='aprobaciones'
    )
    es_reapertura = models.BooleanField(default=False)
    motivo_reapertura = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Aprobación'
        verbose_name_plural = 'Aprobaciones'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['gestion', 'tipo', 'version']),
        ]

    def __str__(self):
        return f'{self.get_tipo_display()} - {self.estado} ({self.gestion} v{self.version})'
