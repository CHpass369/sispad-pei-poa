import uuid, hashlib
from django.db import models
from django.conf import settings
from apps.core.models import TimeStampedModel
from apps.gestion.models import GestionFiscal


class DocumentoAdjunto(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    entidad = models.CharField(max_length=50, help_text='Nombre del modelo asociado')
    entidad_id = models.CharField(max_length=100, help_text='ID del registro')
    nombre = models.CharField(max_length=300)
    descripcion = models.TextField(blank=True)
    # El documento vive cifrado EN LA BASE, no en el disco. Un archivo en
    # MEDIA_ROOT queda a un `location /media/` mal puesto de ser público, y esa
    # configuración no la revisa nadie hasta que el documento ya se filtró.
    # Guardado acá, la única forma de leerlo es pasando por la vista de
    # descarga, donde el permiso ya se verifica.
    contenido_cifrado = models.BinaryField(
        null=True, blank=True, editable=False, verbose_name='Contenido cifrado')
    nonce = models.BinaryField(
        null=True, blank=True, editable=False, verbose_name='Nonce')
    content_type = models.CharField(
        max_length=120, blank=True, default='application/pdf',
        verbose_name='Tipo de contenido')
    # Se conserva para los documentos que ya estuvieran en disco.
    archivo = models.FileField(upload_to='documentos/', blank=True, null=True)
    tipo_documento = models.CharField(max_length=100, blank=True)
    hash_sha256 = models.CharField(max_length=64, blank=True, editable=False)
    tamanio_bytes = models.PositiveBigIntegerField(null=True, blank=True, editable=False)
    subido_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='documentos_subidos'
    )
    gestion = models.ForeignKey(
        GestionFiscal, on_delete=models.PROTECT, db_column='gestion',
        related_name='+', verbose_name='Gestión fiscal',
    )
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Documento adjunto'
        verbose_name_plural = 'Documentos adjuntos'
        indexes = [
            models.Index(fields=['entidad', 'entidad_id']),
            models.Index(fields=['gestion']),
        ]

    def save(self, *args, **kwargs):
        if self.archivo and not self.hash_sha256:
            content = self.archivo.read()
            self.hash_sha256 = hashlib.sha256(content).hexdigest()
            self.tamanio_bytes = len(content)
            self.archivo.seek(0)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nombre
