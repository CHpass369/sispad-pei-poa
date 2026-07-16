import uuid
from django.db import models
from django.core.validators import MinValueValidator
from apps.core.models import TimeStampedModel
from apps.organizacion.models import UnidadEjecutora
from apps.catalogos.models import FuenteFinanciamiento, OrganismoFinanciador


class ProyectoInversion(TimeStampedModel):
    PRIORIDAD_CHOICES = [
        (1, 'Continuidad'),
        (2, 'Financiamiento asegurado'),
        (3, 'Nuevo estratégico'),
        (4, 'Otro nuevo'),
    ]
    ETAPA_CHOICES = [
        ('preinversion', 'Preinversión'),
        ('inversion', 'Inversión'),
        ('cierre', 'Cierre'),
        ('operacion', 'Operación'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    codigo_interno = models.CharField(max_length=50, unique=True)
    codigo_sisin = models.CharField(max_length=100, blank=True, help_text='Código SISIN-WEB')
    nombre = models.CharField(max_length=500)
    descripcion = models.TextField(blank=True)
    tipo = models.ForeignKey('catalogos.TipoProyecto', on_delete=models.PROTECT, null=True, blank=True, related_name='proyectos')
    prioridad = models.PositiveSmallIntegerField(choices=PRIORIDAD_CHOICES, default=4)
    etapa = models.CharField(max_length=20, choices=ETAPA_CHOICES, default='preinversion')
    ue = models.ForeignKey(UnidadEjecutora, on_delete=models.PROTECT, related_name='proyectos_inversion')
    programa = models.ForeignKey('presupuesto.ProgramaPresupuestario', on_delete=models.PROTECT, related_name='proyectos_inversion')
    fuente = models.ForeignKey(FuenteFinanciamiento, on_delete=models.PROTECT, related_name='proyectos_inversion')
    organismo = models.ForeignKey(OrganismoFinanciador, on_delete=models.PROTECT, null=True, blank=True, related_name='proyectos_inversion')
    costo_total = models.DecimalField(max_digits=20, decimal_places=2, validators=[MinValueValidator(0)])
    ejecucion_acumulada = models.DecimalField(max_digits=20, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    gestion_inicio = models.PositiveIntegerField()
    gestion_fin = models.PositiveIntegerField(null=True, blank=True)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Proyecto de inversión'
        verbose_name_plural = 'Proyectos de inversión'
        ordering = ['-gestion_inicio', 'prioridad', 'codigo_interno']

    def __str__(self):
        return f'[{self.codigo_interno}] {self.nombre[:80]}'


class ProgramacionPlurianualProyecto(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    proyecto = models.ForeignKey(ProyectoInversion, on_delete=models.CASCADE, related_name='programacion_plurianual')
    anio = models.PositiveIntegerField()
    monto_programado = models.DecimalField(max_digits=20, decimal_places=2, validators=[MinValueValidator(0)])

    class Meta:
        verbose_name = 'Programación plurianual de proyecto'
        verbose_name_plural = 'Programaciones plurianuales de proyectos'
        unique_together = [('proyecto', 'anio')]
        ordering = ['proyecto', 'anio']


class ProgramacionFisicaFinanciera(TimeStampedModel):
    """Programación física y financiera anual de un proyecto"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    proyecto = models.ForeignKey(ProyectoInversion, on_delete=models.CASCADE, related_name='programacion_fisica_financiera')
    gestion = models.PositiveIntegerField()
    meta_fisica = models.CharField(max_length=500, blank=True)
    unidad_medida = models.CharField(max_length=100, blank=True)
    cantidad_programada = models.DecimalField(max_digits=20, decimal_places=4, null=True, blank=True)
    monto_programado = models.DecimalField(max_digits=20, decimal_places=2, validators=[MinValueValidator(0)])
    trimestre1 = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    trimestre2 = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    trimestre3 = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    trimestre4 = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)

    class Meta:
        verbose_name = 'Programación física y financiera'
        verbose_name_plural = 'Programaciones físicas y financieras'
        unique_together = [('proyecto', 'gestion')]
