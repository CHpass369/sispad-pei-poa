import uuid
from django.db import models
from django.core.validators import MinValueValidator
from apps.core.models import TimeStampedModel
from apps.catalogos.models import (
    ObjetoGasto, FuenteFinanciamiento, OrganismoFinanciador,
    EntidadTransferencia, FinalidadFuncion
)
from apps.organizacion.models import DireccionAdministrativa, UnidadEjecutora


class ProgramaPresupuestario(TimeStampedModel):
    """Estructura programática municipal"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    codigo = models.CharField(max_length=20)
    nombre = models.CharField(max_length=300)
    descripcion = models.TextField(blank=True)
    gestion = models.PositiveIntegerField()
    ue_responsable = models.ForeignKey(
        UnidadEjecutora, on_delete=models.PROTECT,
        null=True, blank=True, related_name='programas'
    )
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Programa presupuestario'
        verbose_name_plural = 'Programas presupuestarios'
        unique_together = [('codigo', 'gestion')]
        ordering = ['gestion', 'codigo']

    def __str__(self):
        return f'{self.codigo} - {self.nombre}'


class ProyectoPresupuestario(TimeStampedModel):
    """Proyecto dentro de la estructura programática"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    codigo = models.CharField(max_length=20)
    nombre = models.CharField(max_length=300)
    programa = models.ForeignKey(ProgramaPresupuestario, on_delete=models.CASCADE, related_name='proyectos')
    gestion = models.PositiveIntegerField()
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Proyecto presupuestario'
        verbose_name_plural = 'Proyectos presupuestarios'
        unique_together = [('codigo', 'programa', 'gestion')]
        ordering = ['programa', 'codigo']

    def __str__(self):
        return f'{self.codigo} - {self.nombre}'


class ActividadPresupuestaria(TimeStampedModel):
    """Actividad dentro de un proyecto presupuestario"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    codigo = models.CharField(max_length=20)
    nombre = models.CharField(max_length=300)
    proyecto = models.ForeignKey(ProyectoPresupuestario, on_delete=models.CASCADE, related_name='actividades')
    gestion = models.PositiveIntegerField()
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Actividad presupuestaria'
        verbose_name_plural = 'Actividades presupuestarias'
        unique_together = [('codigo', 'proyecto', 'gestion')]
        ordering = ['proyecto', 'codigo']

    def __str__(self):
        return f'{self.codigo} - {self.nombre}'


class LineaPresupuestaria(TimeStampedModel):
    """
    Llave presupuestaria completa:
    Entidad + DA + UE + Programa + Proyecto + Actividad + Finalidad/Función
    + Fuente + Organismo + Objeto del gasto + Entidad de transferencia + Importe
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    gestion = models.PositiveIntegerField()
    entidad = models.CharField(max_length=20)
    da = models.ForeignKey(DireccionAdministrativa, on_delete=models.PROTECT, related_name='lineas')
    ue = models.ForeignKey(UnidadEjecutora, on_delete=models.PROTECT, related_name='lineas')
    programa = models.ForeignKey(ProgramaPresupuestario, on_delete=models.PROTECT, related_name='lineas')
    proyecto = models.ForeignKey(ProyectoPresupuestario, on_delete=models.PROTECT, null=True, blank=True, related_name='lineas')
    actividad = models.ForeignKey(ActividadPresupuestaria, on_delete=models.PROTECT, null=True, blank=True, related_name='lineas')
    finalidad_funcion = models.ForeignKey(FinalidadFuncion, on_delete=models.PROTECT, related_name='lineas')
    fuente = models.ForeignKey(FuenteFinanciamiento, on_delete=models.PROTECT, related_name='lineas')
    organismo = models.ForeignKey(OrganismoFinanciador, on_delete=models.PROTECT, null=True, blank=True, related_name='lineas')
    objeto_gasto = models.ForeignKey(ObjetoGasto, on_delete=models.PROTECT, related_name='lineas')
    entidad_transferencia = models.ForeignKey(EntidadTransferencia, on_delete=models.PROTECT, null=True, blank=True, related_name='lineas')
    importe = models.DecimalField(max_digits=20, decimal_places=2, validators=[MinValueValidator(0)])
    importe_plurianual = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0)])
    importe_gestion_anterior = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0)])
    operacion = models.ForeignKey(
        'indicadores.Operacion', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='lineas_presupuestarias'
    )
    version = models.PositiveIntegerField(default=1)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Línea presupuestaria'
        verbose_name_plural = 'Líneas presupuestarias'
        ordering = ['gestion', 'programa__codigo']
        indexes = [
            models.Index(fields=['gestion', 'programa', 'fuente', 'objeto_gasto']),
            models.Index(fields=['gestion', 'ue']),
        ]

    def __str__(self):
        return f'LP {self.gestion} - {self.programa.codigo}/{self.objeto_gasto.codigo}: Bs {self.importe}'
