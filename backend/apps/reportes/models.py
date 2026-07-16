import uuid, hashlib
from django.db import models
from django.conf import settings


class ReporteGenerado(models.Model):
    FORMATO_CHOICES = [
        ('pdf', 'PDF'),
        ('xlsx', 'XLSX'),
        ('csv', 'CSV'),
        ('geojson', 'GeoJSON'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nombre = models.CharField(max_length=300)
    tipo = models.CharField(max_length=50, choices=[
        ('poa_unidad', 'POA por unidad'),
        ('poa_institucional', 'POA institucional consolidado'),
        ('acciones_mediano', 'Acciones de mediano plazo'),
        ('acciones_corto', 'Acciones de corto plazo'),
        ('matriz_resultados', 'Matriz de resultados'),
        ('programacion_fisica', 'Programación física trimestral'),
        ('presupuesto_plurianual', 'Presupuesto plurianual'),
        ('presupuesto_anual', 'Presupuesto anual por programas'),
        ('llave_presupuestaria', 'Llave presupuestaria detallada'),
        ('techos_saldos', 'Techos y saldos'),
        ('proyectos_inversion', 'Proyectos de inversión'),
        ('asignaciones_obligatorias', 'Asignaciones obligatorias'),
        ('observaciones', 'Observaciones'),
        ('expediente_aprobacion', 'Expediente de aprobación'),
        ('auditoria', 'Reporte de auditoría'),
        ('mapa_inversion', 'Mapa de inversión territorial'),
    ])
    formato = models.CharField(max_length=10, choices=FORMATO_CHOICES)
    archivo = models.FileField(upload_to='reportes/', null=True, blank=True)
    hash_archivo = models.CharField(max_length=64, blank=True, editable=False)
    parametros = models.JSONField(null=True, blank=True, help_text='Parámetros usados para generar el reporte')
    gestion = models.PositiveIntegerField()
    generado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='reportes_generados'
    )
    version_datos = models.CharField(max_length=50, blank=True, help_text='Versión de los datos al generar')
    fecha_generacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Reporte generado'
        verbose_name_plural = 'Reportes generados'
        ordering = ['-fecha_generacion']

    def save(self, *args, **kwargs):
        if self.archivo and not self.hash_archivo:
            content = self.archivo.read()
            self.hash_archivo = hashlib.sha256(content).hexdigest()
            self.archivo.seek(0)
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.get_tipo_display()} ({self.get_formato_display()}) - {self.fecha_generacion}'
