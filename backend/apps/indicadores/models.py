import uuid
from django.db import models
from django.conf import settings
from apps.core.models import TimeStampedModel


class Indicador(TimeStampedModel):
    TIPO_COMPORTAMIENTO = [
        ('acumulable', 'Acumulable'),
        ('no_acumulable', 'No Acumulable'),
        ('promedio', 'Promedio'),
        ('hito', 'Hito'),
        ('porcentaje', 'Porcentaje'),
        ('cualitativo', 'Cualitativo'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    codigo = models.CharField(max_length=50)
    nombre = models.TextField()
    descripcion = models.TextField(blank=True)
    formula = models.TextField(blank=True, help_text='Fórmula del indicador')
    unidad_medida = models.ForeignKey(
        'catalogos.UnidadMedida', on_delete=models.PROTECT,
        null=True, blank=True, related_name='indicadores'
    )
    tipo_comportamiento = models.CharField(max_length=20, choices=TIPO_COMPORTAMIENTO, default='acumulable')
    linea_base = models.DecimalField(max_digits=20, decimal_places=4, null=True, blank=True)
    anio_linea_base = models.PositiveIntegerField(null=True, blank=True)
    fuente_linea_base = models.CharField(max_length=500, blank=True)
    meta_anual = models.DecimalField(max_digits=20, decimal_places=4, null=True, blank=True)
    medio_verificacion = models.TextField(blank=True)
    frecuencia_medicion = models.CharField(max_length=100, blank=True)
    responsable = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='indicadores'
    )
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Indicador'
        verbose_name_plural = 'Indicadores'
        ordering = ['codigo']

    def __str__(self):
        return f'[{self.codigo}] {self.nombre[:80]}'


class MetaProgramada(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    indicador = models.ForeignKey(Indicador, on_delete=models.CASCADE, related_name='metas_programadas')
    gestion = models.PositiveIntegerField()
    meta_anual = models.DecimalField(max_digits=20, decimal_places=4)
    trimestre1 = models.DecimalField(max_digits=20, decimal_places=4, null=True, blank=True)
    trimestre2 = models.DecimalField(max_digits=20, decimal_places=4, null=True, blank=True)
    trimestre3 = models.DecimalField(max_digits=20, decimal_places=4, null=True, blank=True)
    trimestre4 = models.DecimalField(max_digits=20, decimal_places=4, null=True, blank=True)
    observaciones = models.TextField(blank=True)
    version = models.PositiveIntegerField(default=1)

    class Meta:
        verbose_name = 'Meta programada'
        verbose_name_plural = 'Metas programadas'
        unique_together = [('indicador', 'gestion', 'version')]
        ordering = ['indicador', 'gestion', '-version']

    def __str__(self):
        return f'{self.indicador.codigo} - {self.gestion} v{self.version}'


class Operacion(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    accion_corto_plazo = models.ForeignKey(
        'planificacion.AccionCortoPlazo', on_delete=models.CASCADE,
        related_name='operaciones'
    )
    codigo = models.CharField(max_length=50)
    nombre = models.TextField()
    descripcion = models.TextField(blank=True)
    tipo = models.ForeignKey(
        'catalogos.TipoOperacion', on_delete=models.PROTECT,
        null=True, blank=True, related_name='operaciones'
    )
    fecha_inicio = models.DateField(null=True, blank=True)
    fecha_fin = models.DateField(null=True, blank=True)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Operación'
        verbose_name_plural = 'Operaciones'
        ordering = ['accion_corto_plazo', 'codigo']
        unique_together = [('accion_corto_plazo', 'codigo')]

    def __str__(self):
        return f'{self.codigo} - {self.nombre[:60]}'


class Tarea(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    operacion = models.ForeignKey(Operacion, on_delete=models.CASCADE, related_name='tareas')
    codigo = models.CharField(max_length=50)
    nombre = models.TextField()
    descripcion = models.TextField(blank=True)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Tarea'
        verbose_name_plural = 'Tareas'
        unique_together = [('operacion', 'codigo')]

    def __str__(self):
        return f'{self.codigo} - {self.nombre[:60]}'


class Producto(TimeStampedModel):
    """Producto esperado: bien, servicio o norma"""
    TIPO_PRODUCTO = [
        ('terminal', 'Terminal'),
        ('intermedio', 'Intermedio'),
    ]
    ESTADO_PRODUCTO = [
        ('acabado', 'Acabado'),
        ('proceso', 'En proceso'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    accion_corto_plazo = models.ForeignKey(
        'planificacion.AccionCortoPlazo', on_delete=models.CASCADE,
        related_name='productos'
    )
    codigo = models.CharField(max_length=50)
    nombre = models.TextField()
    tipo = models.CharField(max_length=20, choices=TIPO_PRODUCTO, default='terminal')
    estado = models.CharField(max_length=20, choices=ESTADO_PRODUCTO, default='acabado')
    tipo_producto = models.ForeignKey(
        'catalogos.TipoProducto', on_delete=models.PROTECT,
        null=True, blank=True, related_name='productos'
    )
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Producto'
        verbose_name_plural = 'Productos'
        unique_together = [('accion_corto_plazo', 'codigo')]

    def __str__(self):
        return f'{self.codigo} - {self.nombre[:60]}'


class MedioVerificacion(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    indicador = models.ForeignKey(
        Indicador, on_delete=models.CASCADE,
        related_name='medios_verificacion'
    )
    nombre = models.CharField(max_length=300)
    descripcion = models.TextField(blank=True)
    soporte_esperado = models.CharField(max_length=500, blank=True)

    class Meta:
        verbose_name = 'Medio de verificación'
        verbose_name_plural = 'Medios de verificación'

    def __str__(self):
        return self.nombre


class Supuesto(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    accion_corto_plazo = models.ForeignKey(
        'planificacion.AccionCortoPlazo', on_delete=models.CASCADE,
        related_name='supuestos'
    )
    descripcion = models.TextField()
    riesgo_externo = models.TextField(blank=True)
    probabilidad = models.CharField(max_length=50, blank=True)

    class Meta:
        verbose_name = 'Supuesto'
        verbose_name_plural = 'Supuestos'

    def __str__(self):
        return self.descripcion[:80]
