import uuid
from django.db import models
from django.conf import settings


class EventoAuditoria(models.Model):
    class Accion(models.TextChoices):
        LOGIN = 'login', 'Inicio de sesión'
        LOGOUT = 'logout', 'Cierre de sesión'
        CREAR = 'crear', 'Creación'
        MODIFICAR = 'modificar', 'Modificación'
        ANULAR = 'anular', 'Anulación'
        RESTAURAR = 'restaurar', 'Restauración'
        ENVIAR = 'enviar', 'Envío'
        DEVOLVER = 'devolver', 'Devolución'
        APROBAR = 'aprobar', 'Aprobación'
        REABRIR = 'reabrir', 'Reapertura'
        IMPORTAR = 'importar', 'Importación'
        EXPORTAR = 'exportar', 'Exportación'
        CONSOLIDAR = 'consolidar', 'Consolidación'
        CERRAR = 'cerrar', 'Cierre'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='eventos_auditoria'
    )
    accion = models.CharField(max_length=20, choices=Accion)
    entidad = models.CharField(max_length=100, help_text='Nombre del modelo')
    entidad_id = models.CharField(max_length=100, help_text='ID del registro afectado')
    version = models.PositiveIntegerField(null=True, blank=True)
    resumen = models.TextField(blank=True, help_text='Descripción del cambio')
    datos_previos = models.JSONField(null=True, blank=True)
    datos_posteriores = models.JSONField(null=True, blank=True)
    direccion_ip = models.GenericIPAddressField(null=True, blank=True)
    gestion = models.PositiveIntegerField(null=True, blank=True)
    creado_en = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = 'Evento de auditoría'
        verbose_name_plural = 'Eventos de auditoría'
        ordering = ['-creado_en']
        indexes = [
            models.Index(fields=['entidad', 'entidad_id']),
            models.Index(fields=['usuario', 'creado_en']),
            models.Index(fields=['gestion']),
        ]

    def __str__(self):
        return f'{self.get_accion_display()} - {self.entidad}#{self.entidad_id} - {self.creado_en}'
