import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone
from apps.core.models import TimeStampedModel


class TipoNotificacion(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    codigo = models.CharField(max_length=50, unique=True, verbose_name='Código')
    nombre = models.CharField(max_length=200, verbose_name='Nombre')
    descripcion = models.TextField(blank=True, verbose_name='Descripción')
    template_subject = models.CharField(
        max_length=300, blank=True,
        verbose_name='Asunto del template',
        help_text='Plantilla para el asunto del correo. Use {variable} para interpolación.'
    )
    template_body = models.TextField(
        blank=True, verbose_name='Cuerpo del template',
        help_text='Plantilla para el cuerpo del correo. Use {variable} para interpolación.'
    )
    is_active = models.BooleanField(default=True, verbose_name='Activo')

    class Meta:
        verbose_name = 'Tipo de notificación'
        verbose_name_plural = 'Tipos de notificación'
        ordering = ['codigo']

    def __str__(self):
        return f'{self.codigo} - {self.nombre}'


class Notificacion(TimeStampedModel):
    class Prioridad(models.TextChoices):
        ALTA = 'alta', 'Alta'
        MEDIA = 'media', 'Media'
        BAJA = 'baja', 'Baja'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='notificaciones', verbose_name='Usuario'
    )
    tipo = models.ForeignKey(
        TipoNotificacion, on_delete=models.PROTECT,
        related_name='notificaciones', verbose_name='Tipo'
    )
    titulo = models.CharField(max_length=300, verbose_name='Título')
    mensaje = models.TextField(verbose_name='Mensaje')
    is_read = models.BooleanField(default=False, verbose_name='Leído')
    read_at = models.DateTimeField(null=True, blank=True, verbose_name='Fecha de lectura')
    priority = models.CharField(
        max_length=10, choices=Prioridad.choices,
        default=Prioridad.MEDIA, verbose_name='Prioridad'
    )
    entity_type = models.CharField(
        max_length=100, null=True, blank=True,
        verbose_name='Tipo de entidad',
        help_text='Tipo de entidad relacionada (ej: gestion, indicador, tarea)'
    )
    entity_id = models.UUIDField(
        null=True, blank=True,
        verbose_name='ID de entidad',
        help_text='UUID del registro relacionado'
    )
    gestion = models.PositiveIntegerField(verbose_name='Gestión fiscal')
    metadata = models.JSONField(
        null=True, blank=True,
        verbose_name='Metadatos adicionales'
    )

    class Meta:
        verbose_name = 'Notificación'
        verbose_name_plural = 'Notificaciones'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read']),
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['gestion']),
            models.Index(fields=['priority']),
        ]

    def __str__(self):
        return f'{self.titulo} - {self.user}'

    def marcar_leida(self):
        self.is_read = True
        self.read_at = timezone.now()
        self.save(update_fields=['is_read', 'read_at', 'updated_at'])


class PreferenciaNotificacion(TimeStampedModel):
    class Frecuencia(models.TextChoices):
        INMEDIATA = 'inmediata', 'Inmediata'
        DIARIA = 'diaria', 'Diaria'
        SEMANAL = 'semanal', 'Semanal'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='preferencia_notificacion', verbose_name='Usuario'
    )
    receive_internal = models.BooleanField(
        default=True, verbose_name='Recibir notificaciones internas'
    )
    receive_email = models.BooleanField(
        default=False, verbose_name='Recibir notificaciones por correo'
    )
    frequency = models.CharField(
        max_length=10, choices=Frecuencia.choices,
        default=Frecuencia.INMEDIATA, verbose_name='Frecuencia de envío'
    )

    class Meta:
        verbose_name = 'Preferencia de notificación'
        verbose_name_plural = 'Preferencias de notificación'

    def __str__(self):
        return f'Preferencias de {self.user}'
