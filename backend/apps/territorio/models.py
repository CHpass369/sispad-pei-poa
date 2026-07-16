import uuid
from django.db import models
from django.contrib.gis.db import models as gis_models
from apps.core.models import TimeStampedModel


class Distrito(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    codigo = models.CharField(max_length=10)
    nombre = models.CharField(max_length=200)
    geometria = gis_models.MultiPolygonField(srid=4326, null=True, blank=True)

    class Meta:
        verbose_name = 'Distrito'
        verbose_name_plural = 'Distritos'

    def __str__(self):
        return f'{self.codigo} - {self.nombre}'


class UnidadTerritorial(models.Model):
    """OTB, comunidad, zona, etc."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    codigo = models.CharField(max_length=20)
    nombre = models.CharField(max_length=300)
    tipo = models.CharField(max_length=50, choices=[
        ('otb', 'OTB'),
        ('comunidad', 'Comunidad'),
        ('zona', 'Zona'),
        ('establecimiento', 'Establecimiento'),
        ('otro', 'Otro'),
    ])
    distrito = models.ForeignKey(Distrito, on_delete=models.SET_NULL, null=True, blank=True, related_name='unidades_territoriales')
    geometria = gis_models.MultiPolygonField(srid=4326, null=True, blank=True)
    centroide = gis_models.PointField(srid=4326, null=True, blank=True)
    poblacion = models.PositiveIntegerField(null=True, blank=True)
    superficie_ha = models.DecimalField(max_digits=15, decimal_places=4, null=True, blank=True)

    class Meta:
        verbose_name = 'Unidad territorial'
        verbose_name_plural = 'Unidades territoriales'
        ordering = ['distrito', 'tipo', 'nombre']

    def __str__(self):
        return f'{self.nombre} ({self.get_tipo_display()})'


class LocalizacionTerritorial(TimeStampedModel):
    """Vincula acciones/proyectos con geometrías y unidades territoriales"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    entidad = models.CharField(max_length=50, help_text='Nombre del modelo asociado')
    entidad_id = models.CharField(max_length=100, help_text='ID del registro')
    geometria = gis_models.GeometryField(srid=32719, null=True, blank=True, help_text='Geometría en EPSG:32719 (métrica)')
    geometria_4326 = gis_models.GeometryField(srid=4326, null=True, blank=True, help_text='Geometría en EPSG:4326 (web)')
    distrito = models.ForeignKey(Distrito, on_delete=models.SET_NULL, null=True, blank=True, related_name='localizaciones')
    unidad_territorial = models.ForeignKey(UnidadTerritorial, on_delete=models.SET_NULL, null=True, blank=True, related_name='localizaciones')
    direccion_referencia = models.CharField(max_length=500, blank=True)
    gestion = models.PositiveIntegerField()
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Localización territorial'
        verbose_name_plural = 'Localizaciones territoriales'
        indexes = [
            models.Index(fields=['entidad', 'entidad_id']),
            models.Index(fields=['gestion']),
        ]

    def __str__(self):
        return f'{self.entidad}#{self.entidad_id} en {self.distrito}'
