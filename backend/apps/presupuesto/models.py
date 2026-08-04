import uuid
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models
from django.core.validators import MinValueValidator
from apps.core.models import TimeStampedModel
from apps.catalogos.models import (
    ClasificadorInstitucional, EntidadTransferencia, FinalidadFuncion,
    FuenteFinanciamiento, ObjetoGasto, OrganismoFinanciador,
    VersionClasificador,
)
from apps.organizacion.models import (
    DireccionAdministrativa, UnidadEjecutora, UnidadOrganizacional,
)


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


class CategoriaProgramaticaQuerySet(models.QuerySet):
    def update(self, **kwargs):
        if 'codigo_compuesto' in kwargs:
            raise ValidationError('El código compuesto solo puede generarlo el backend.')
        return super().update(**kwargs)

    def bulk_update(self, objs, fields, batch_size=None):
        if 'codigo_compuesto' in fields:
            raise ValidationError('El código compuesto no admite bulk_update.')
        return super().bulk_update(objs, fields, batch_size=batch_size)

    def bulk_create(self, objs, *args, **kwargs):
        objetos = list(objs)
        if any(objeto.codigo_compuesto for objeto in objetos):
            raise ValidationError('El código compuesto solo puede generarlo el backend.')
        return super().bulk_create(objetos, *args, **kwargs)


class CategoriaProgramaticaManager(models.Manager.from_queryset(
    CategoriaProgramaticaQuerySet,
)):
    pass


class CategoriaProgramatica(TimeStampedModel):
    """Apertura programática literal, sin asumir anchos no documentados."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    version_clasificador = models.ForeignKey(
        VersionClasificador,
        on_delete=models.PROTECT,
        related_name='categorias_programaticas',
    )
    entidad = models.ForeignKey(
        ClasificadorInstitucional,
        on_delete=models.PROTECT,
        related_name='categorias_programaticas',
    )
    da = models.ForeignKey(
        DireccionAdministrativa,
        on_delete=models.PROTECT,
        related_name='categorias_programaticas',
    )
    ue = models.ForeignKey(
        UnidadEjecutora,
        on_delete=models.PROTECT,
        related_name='categorias_programaticas',
    )
    programa = models.ForeignKey(
        ProgramaPresupuestario,
        on_delete=models.PROTECT,
        related_name='categorias_programaticas',
    )
    proyecto = models.ForeignKey(
        ProyectoPresupuestario,
        on_delete=models.PROTECT,
        related_name='categorias_programaticas',
    )
    actividad = models.ForeignKey(
        ActividadPresupuestaria,
        on_delete=models.PROTECT,
        related_name='categorias_programaticas',
    )
    codigo_compuesto = models.CharField(max_length=200, editable=False)
    codigo_fuente = models.CharField(max_length=200)
    procedencia_normativa = models.CharField(max_length=500)

    objects = CategoriaProgramaticaManager()

    class Meta:
        verbose_name = 'Categoría programática'
        verbose_name_plural = 'Categorías programáticas'
        constraints = [
            models.UniqueConstraint(
                fields=[
                    'version_clasificador', 'entidad', 'da', 'ue',
                    'programa', 'proyecto', 'actividad',
                ],
                name='uniq_categoria_programatica_apertura',
            ),
            models.UniqueConstraint(
                fields=['version_clasificador', 'codigo_compuesto'],
                name='uniq_categoria_programatica_codigo',
            ),
        ]
        indexes = [
            models.Index(fields=['version_clasificador', 'entidad']),
            models.Index(fields=['da', 'ue']),
            models.Index(fields=['programa', 'proyecto', 'actividad']),
        ]

    def _generar_codigo_compuesto(self):
        return '.'.join(
            (
                self.entidad.codigo,
                self.da.codigo,
                self.ue.codigo,
                self.programa.codigo,
                self.proyecto.codigo,
                self.actividad.codigo,
            )
        )

    def clean(self):
        super().clean()
        errors = {}
        if self.entidad_id and self.entidad.codigo != '1312':
            errors['entidad'] = 'La categoría programática debe pertenecer a la entidad 1312.'
        gestion = self.version_clasificador.gestion if self.version_clasificador_id else None
        if self.version_clasificador_id and (
            self.version_clasificador.tipo
            != VersionClasificador.TIPO_CATEGORIA_PROGRAMATICA
        ):
            errors['version_clasificador'] = 'La versión debe ser de categoría programática.'
        for field in ('entidad', 'da', 'ue', 'programa', 'proyecto', 'actividad'):
            related = getattr(self, field, None)
            if related is not None and gestion is not None and related.gestion != gestion:
                errors[field] = 'La gestión del componente no coincide con la versión.'
        if self.ue_id and self.da_id and self.ue.da_id != self.da_id:
            errors['ue'] = 'La unidad ejecutora no pertenece a la dirección administrativa.'
        if self.proyecto_id and self.programa_id and self.proyecto.programa_id != self.programa_id:
            errors['proyecto'] = 'El proyecto no pertenece al programa.'
        if self.actividad_id and self.proyecto_id and self.actividad.proyecto_id != self.proyecto_id:
            errors['actividad'] = 'La actividad no pertenece al proyecto.'
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.codigo_compuesto = self._generar_codigo_compuesto()
        self.full_clean(validate_constraints=False)
        return super().save(*args, **kwargs)

    def __str__(self):
        return self.codigo_compuesto


class AsignacionPresupuestariaUnidad(TimeStampedModel):
    """Detalle presupuestario asociado a un único nivel operativo canónico."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    categoria_programatica = models.ForeignKey(
        CategoriaProgramatica,
        on_delete=models.PROTECT,
        related_name='asignaciones',
    )
    fuente = models.ForeignKey(
        FuenteFinanciamiento,
        on_delete=models.PROTECT,
        related_name='asignaciones_presupuestarias_unidad',
    )
    organismo = models.ForeignKey(
        OrganismoFinanciador,
        on_delete=models.PROTECT,
        related_name='asignaciones_presupuestarias_unidad',
    )
    objeto_gasto = models.ForeignKey(
        ObjetoGasto,
        on_delete=models.PROTECT,
        related_name='asignaciones_presupuestarias_unidad',
    )
    unidad = models.ForeignKey(
        UnidadOrganizacional,
        on_delete=models.PROTECT,
        related_name='asignaciones_presupuestarias',
    )
    operacion = models.ForeignKey(
        'articulacion.OperacionPOAU',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='asignaciones_presupuestarias',
    )
    actividad = models.ForeignKey(
        'articulacion.ActividadPOAU',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='asignaciones_presupuestarias',
    )
    tarea = models.ForeignKey(
        'articulacion.TareaPOAU',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='asignaciones_presupuestarias',
    )
    gestion = models.PositiveIntegerField()
    monto_formulado = models.DecimalField(max_digits=20, decimal_places=2)
    monto_vigente = models.DecimalField(max_digits=20, decimal_places=2)
    monto_ejecutado = models.DecimalField(max_digits=20, decimal_places=2)

    class Meta:
        verbose_name = 'Asignación presupuestaria por unidad'
        verbose_name_plural = 'Asignaciones presupuestarias por unidad'
        constraints = [
            models.CheckConstraint(
                condition=(
                    (
                        models.Q(operacion__isnull=False)
                        & models.Q(actividad__isnull=True)
                        & models.Q(tarea__isnull=True)
                    )
                    | (
                        models.Q(operacion__isnull=True)
                        & models.Q(actividad__isnull=False)
                        & models.Q(tarea__isnull=True)
                    )
                    | (
                        models.Q(operacion__isnull=True)
                        & models.Q(actividad__isnull=True)
                        & models.Q(tarea__isnull=False)
                    )
                ),
                name='asignacion_exactamente_un_nivel',
            ),
            models.CheckConstraint(
                condition=models.Q(monto_formulado__gte=0),
                name='asignacion_formulado_no_negativo',
            ),
            models.CheckConstraint(
                condition=models.Q(monto_vigente__gte=0),
                name='asignacion_vigente_no_negativo',
            ),
            models.CheckConstraint(
                condition=models.Q(monto_ejecutado__gte=0),
                name='asignacion_ejecutado_no_negativo',
            ),
            models.CheckConstraint(
                condition=models.Q(monto_ejecutado__lte=models.F('monto_vigente')),
                name='asignacion_ejecutado_hasta_vigente',
            ),
            models.UniqueConstraint(
                fields=[
                    'categoria_programatica', 'fuente', 'organismo',
                    'objeto_gasto', 'unidad', 'operacion', 'actividad',
                    'tarea', 'gestion',
                ],
                name='uniq_asignacion_presupuestaria_unidad',
                nulls_distinct=False,
            ),
        ]
        indexes = [
            models.Index(fields=['gestion', 'unidad']),
            models.Index(fields=['objeto_gasto', 'gestion']),
            models.Index(fields=['categoria_programatica']),
        ]

    @property
    def nivel_operativo(self):
        for field in ('operacion', 'actividad', 'tarea'):
            if getattr(self, f'{field}_id') is not None:
                return field
        return None

    @property
    def saldo_por_ejecutar(self):
        return (self.monto_vigente or Decimal('0')) - (
            self.monto_ejecutado or Decimal('0')
        )

    def clean(self):
        super().clean()
        errors = {}
        relations = {
            'categoria_programatica': (
                self.categoria_programatica.version_clasificador.gestion
                if self.categoria_programatica_id else None
            ),
            'unidad': self.unidad.gestion if self.unidad_id else None,
            'fuente': (
                self.fuente.version_clasificador.gestion
                if self.fuente_id and self.fuente.version_clasificador_id else None
            ),
            'organismo': (
                self.organismo.version_clasificador.gestion
                if self.organismo_id and self.organismo.version_clasificador_id else None
            ),
            'objeto_gasto': (
                self.objeto_gasto.version_clasificador.gestion
                if self.objeto_gasto_id and self.objeto_gasto.version_clasificador_id else None
            ),
        }
        for field, related_gestion in relations.items():
            if related_gestion != self.gestion:
                errors[field] = 'La relación debe estar versionada en la gestión de la asignación.'

        expected_types = {
            'fuente': VersionClasificador.TIPO_FUENTE_FINANCIAMIENTO,
            'organismo': VersionClasificador.TIPO_ORGANISMO_FINANCIADOR,
            'objeto_gasto': VersionClasificador.TIPO_OBJETO_GASTO,
        }
        for field, expected_type in expected_types.items():
            related = getattr(self, field, None)
            version = getattr(related, 'version_clasificador', None)
            if version is not None and version.tipo != expected_type:
                errors[field] = 'El catálogo está vinculado a una versión de tipo incorrecto.'

        operational_management = {
            'operacion': (
                self.operacion.accion_poa.gestion if self.operacion_id else None
            ),
            'actividad': (
                self.actividad.operacion.accion_poa.gestion if self.actividad_id else None
            ),
            'tarea': (
                self.tarea.actividad.operacion.accion_poa.gestion if self.tarea_id else None
            ),
        }
        for field, related_gestion in operational_management.items():
            if related_gestion is not None and related_gestion != self.gestion:
                errors[field] = 'El nivel operativo no pertenece a la gestión de la asignación.'
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean(validate_constraints=False)
        return super().save(*args, **kwargs)


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
