import uuid
from django.db import models
from django.conf import settings
from apps.core.models import TimeStampedModel, ActivableModel, VigenciaModel, VersionableModel


class Plan(TimeStampedModel, ActivableModel, VigenciaModel):
    TIPO_CHOICES = [
        ('pdes', 'PDES'),
        ('ptdi', 'PTDI'),
        ('pei', 'PEI'),
        ('sectorial', 'Plan Sectorial'),
        ('municipal', 'Plan Municipal'),
        ('otro', 'Otro'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    codigo = models.CharField(max_length=50)
    nombre = models.CharField(max_length=500)
    tipo = models.CharField(max_length=50, choices=TIPO_CHOICES)
    gestion_inicio = models.PositiveIntegerField()
    gestion_fin = models.PositiveIntegerField()
    descripcion = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Plan'
        verbose_name_plural = 'Planes'
        unique_together = [('codigo', 'tipo')]
        ordering = ['tipo', 'gestion_inicio']

    def __str__(self):
        return f'{self.get_tipo_display()} - {self.nombre}'


class Sector(TimeStampedModel, ActivableModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    codigo = models.CharField(max_length=50, unique=True)
    nombre = models.CharField(max_length=500)

    class Meta:
        verbose_name = 'Sector'
        verbose_name_plural = 'Sectores'
        ordering = ['codigo']

    def __str__(self):
        return f'[{self.codigo}] {self.nombre}'


class NodoPlanificacion(TimeStampedModel, ActivableModel):
    NIVEL_CHOICES = [
        ('pilar', 'Pilar'),
        ('eje', 'Eje Estratégico'),
        ('meta', 'Meta'),
        ('resultado', 'Resultado'),
        ('accion_nacional', 'Acción Nacional'),
        ('accion_pdes', 'Acción PDES/PTDI/PEI'),
        ('accion_mediano', 'Acción de Mediano Plazo'),
        ('accion_corto', 'Acción de Corto Plazo'),
        ('operacion', 'Operación'),
        ('tarea', 'Tarea'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    plan = models.ForeignKey(Plan, on_delete=models.CASCADE, related_name='nodos')
    padre = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='hijos')
    nivel = models.CharField(max_length=30, choices=NIVEL_CHOICES)
    codigo = models.CharField(max_length=50)
    nombre = models.TextField()
    descripcion = models.TextField(blank=True)
    gestion = models.PositiveIntegerField()
    orden = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = 'Nodo de planificación'
        verbose_name_plural = 'Nodos de planificación'
        ordering = ['plan', 'nivel', 'orden']
        unique_together = [('plan', 'codigo', 'nivel')]
        indexes = [
            models.Index(fields=['nivel', 'gestion']),
        ]

    def __str__(self):
        return f'[{self.get_nivel_display()}] {self.codigo} - {self.nombre[:80]}'


class AccionMedianoPlazo(TimeStampedModel, ActivableModel):
    """Acción de mediano plazo del PEI, vinculable a programas presupuestarios"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    codigo = models.CharField(max_length=50)
    nombre = models.TextField()
    descripcion = models.TextField(blank=True)
    nodo_planificacion = models.ForeignKey(
        NodoPlanificacion, on_delete=models.PROTECT,
        related_name='acciones_mediano_plazo',
        limit_choices_to={'nivel': 'accion_mediano'}
    )
    gestion_inicio = models.PositiveIntegerField()
    gestion_fin = models.PositiveIntegerField()
    responsable = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='acciones_mediano_plazo'
    )

    class Meta:
        verbose_name = 'Acción de mediano plazo'
        verbose_name_plural = 'Acciones de mediano plazo'
        ordering = ['codigo']

    def __str__(self):
        return f'AMP {self.codigo} - {self.nombre[:80]}'


class AccionCortoPlazo(TimeStampedModel, ActivableModel):
    """Acción de corto plazo del POA, articulada a una acción de mediano plazo"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    codigo = models.CharField(max_length=50)
    nombre = models.TextField()
    descripcion = models.TextField(blank=True)
    justificacion = models.TextField(blank=True)
    accion_mediano_plazo = models.ForeignKey(
        AccionMedianoPlazo, on_delete=models.PROTECT,
        related_name='acciones_corto_plazo'
    )
    unidad_responsable = models.ForeignKey(
        'organizacion.UnidadOrganizacional', on_delete=models.PROTECT,
        related_name='acciones_corto_plazo'
    )
    gestion = models.PositiveIntegerField()
    fecha_inicio = models.DateField(null=True, blank=True)
    fecha_fin = models.DateField(null=True, blank=True)

    class Meta:
        verbose_name = 'Acción de corto plazo'
        verbose_name_plural = 'Acciones de corto plazo'
        ordering = ['gestion', 'codigo']
        unique_together = [('codigo', 'gestion')]

    def __str__(self):
        return f'ACP {self.codigo} - {self.nombre[:80]}'


class ArticulacionPlanificacion(TimeStampedModel):
    """Articulaciones múltiples entre nodos de planificación"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nodo_origen = models.ForeignKey(
        NodoPlanificacion, on_delete=models.CASCADE,
        related_name='articulaciones_salida'
    )
    nodo_destino = models.ForeignKey(
        NodoPlanificacion, on_delete=models.CASCADE,
        related_name='articulaciones_entrada'
    )
    es_principal = models.BooleanField(default=False)
    gestion = models.PositiveIntegerField()

    class Meta:
        verbose_name = 'Articulación de planificación'
        verbose_name_plural = 'Articulaciones de planificación'
        unique_together = [('nodo_origen', 'nodo_destino', 'gestion')]


class PlanVersion(TimeStampedModel):
    STATUS_CHOICES = [
        ('borrador', 'Borrador'),
        ('aprobado', 'Aprobado'),
        ('obsoleto', 'Obsoleto'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    plan = models.ForeignKey(Plan, on_delete=models.CASCADE, related_name='versiones')
    version_number = models.PositiveIntegerField()
    version_name = models.CharField(max_length=200)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='borrador')
    valid_from = models.DateField()
    valid_to = models.DateField(null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='planificaciones_aprobadas'
    )
    change_reason = models.TextField()
    immutable = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Versión de plan'
        verbose_name_plural = 'Versiones de plan'
        ordering = ['plan', '-version_number']
        unique_together = [('plan', 'version_number')]

    def __str__(self):
        return f'{self.plan} v{self.version_number} - {self.version_name}'
