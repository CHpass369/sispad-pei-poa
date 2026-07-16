import uuid
from django.db import models
from apps.core.models import TimeStampedModel, ActivableModel, VigenciaModel


class CatalogoBase(TimeStampedModel, ActivableModel, VigenciaModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    codigo = models.CharField(max_length=50)
    denominacion = models.CharField(max_length=500)
    descripcion = models.TextField(blank=True)
    gestion = models.PositiveIntegerField()
    fuente_normativa = models.CharField(max_length=500, blank=True)
    metadatos_importacion = models.JSONField(null=True, blank=True)

    class Meta:
        abstract = True
        unique_together = [('codigo', 'gestion')]

    def __str__(self):
        return f'[{self.codigo}] {self.denominacion}'


class ClasificadorInstitucional(CatalogoBase):
    class Meta:
        verbose_name = 'Clasificador institucional'
        verbose_name_plural = 'Clasificadores institucionales'


class RubroRecurso(CatalogoBase):
    class Meta:
        verbose_name = 'Rubro de recurso'
        verbose_name_plural = 'Rubros de recursos'


class ObjetoGasto(CatalogoBase):
    class Meta:
        verbose_name = 'Objeto del gasto'
        verbose_name_plural = 'Objetos del gasto'


class FuenteFinanciamiento(CatalogoBase):
    class Meta:
        verbose_name = 'Fuente de financiamiento'
        verbose_name_plural = 'Fuentes de financiamiento'


class OrganismoFinanciador(CatalogoBase):
    class Meta:
        verbose_name = 'Organismo financiador'
        verbose_name_plural = 'Organismos financiadores'


class EntidadTransferencia(CatalogoBase):
    """Entidad otorgante o de transferencia"""
    class Meta:
        verbose_name = 'Entidad de transferencia'
        verbose_name_plural = 'Entidades de transferencia'


class FinalidadFuncion(CatalogoBase):
    class Meta:
        verbose_name = 'Finalidad/Función'
        verbose_name_plural = 'Finalidades y funciones'


class UnidadMedida(CatalogoBase):
    class Meta:
        verbose_name = 'Unidad de medida'
        verbose_name_plural = 'Unidades de medida'


class TipoOperacion(CatalogoBase):
    class Meta:
        verbose_name = 'Tipo de operación'
        verbose_name_plural = 'Tipos de operación'


class TipoProducto(CatalogoBase):
    class Meta:
        verbose_name = 'Tipo de producto'
        verbose_name_plural = 'Tipos de producto'


class TipoProyecto(CatalogoBase):
    class Meta:
        verbose_name = 'Tipo de proyecto'
        verbose_name_plural = 'Tipos de proyecto'


class TipoFinanciamiento(CatalogoBase):
    class Meta:
        verbose_name = 'Tipo de financiamiento'
        verbose_name_plural = 'Tipos de financiamiento'


class VersionCatalogo(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nombre = models.CharField(max_length=200)
    gestion = models.PositiveIntegerField()
    archivo = models.FileField(upload_to='catalogos/', null=True, blank=True)
    aplicado = models.BooleanField(default=False)
    fecha_aplicacion = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Versión de catálogo'
        verbose_name_plural = 'Versiones de catálogo'
        ordering = ['-gestion', '-creado_en']

    creado_en = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.nombre} - {self.gestion}'
