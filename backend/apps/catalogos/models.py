import uuid
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models
from django.db.models import Q
from apps.core.models import TimeStampedModel, ActivableModel, VigenciaModel


class VersionClasificadorManager(models.Manager):
    def vigente_para(self, tipo, gestion):
        """Fail closed: an absent explicit current version is an error."""
        return self.get(tipo=tipo, gestion=gestion, vigente=True)


class VersionClasificador(TimeStampedModel):
    TIPO_INSTITUCIONAL = 'institucional'
    TIPO_OBJETO_GASTO = 'objeto_gasto'
    TIPO_FUENTE_FINANCIAMIENTO = 'fuente_financiamiento'
    TIPO_ORGANISMO_FINANCIADOR = 'organismo_financiador'
    TIPO_CATEGORIA_PROGRAMATICA = 'categoria_programatica'
    TIPO_GEOGRAFICO_PRESUPUESTARIO = 'geografico_presupuestario'
    TIPO_CHOICES = [
        (TIPO_INSTITUCIONAL, 'Institucional'),
        (TIPO_OBJETO_GASTO, 'Objeto del gasto'),
        (TIPO_FUENTE_FINANCIAMIENTO, 'Fuente de financiamiento'),
        (TIPO_ORGANISMO_FINANCIADOR, 'Organismo financiador'),
        (TIPO_CATEGORIA_PROGRAMATICA, 'Categoría programática'),
        (TIPO_GEOGRAFICO_PRESUPUESTARIO, 'Geográfico presupuestario'),
    ]

    FUENTE_OFICIAL = 'oficial'
    FUENTE_REFERENCIAL = 'referencial'
    FUENTE_TECNICA = 'tecnica'
    FUENTE_INCIERTA = 'incierta'
    FUENTE_CHOICES = [
        (FUENTE_OFICIAL, 'Oficial'),
        (FUENTE_REFERENCIAL, 'Referencial'),
        (FUENTE_TECNICA, 'Técnica'),
        (FUENTE_INCIERTA, 'Incierta'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tipo = models.CharField(max_length=40, choices=TIPO_CHOICES)
    gestion = models.PositiveIntegerField()
    norma = models.CharField(max_length=300, blank=True)
    fecha_norma = models.DateField(null=True, blank=True)
    codigo_fuente = models.CharField(max_length=100, blank=True)
    procedencia_normativa = models.CharField(max_length=500, blank=True)
    hash_fuente = models.CharField(
        max_length=64,
        blank=True,
        validators=[RegexValidator(r'^[0-9a-f]{64}$', 'El hash debe ser un SHA-256 hexadecimal.')],
    )
    clasificacion_fuente = models.CharField(
        max_length=20,
        choices=FUENTE_CHOICES,
        default=FUENTE_INCIERTA,
    )
    vigente = models.BooleanField(default=False)

    objects = VersionClasificadorManager()

    class Meta:
        ordering = ['tipo', '-gestion', '-fecha_norma']
        constraints = [
            models.UniqueConstraint(
                fields=['tipo', 'gestion'],
                condition=Q(vigente=True),
                name='uniq_clasificador_vigente_tipo_gestion',
            ),
            models.CheckConstraint(
                condition=(
                    Q(vigente=False)
                    | (
                        Q(clasificacion_fuente='oficial')
                        & ~Q(norma='')
                        & Q(fecha_norma__isnull=False)
                        & ~Q(codigo_fuente='')
                        & ~Q(procedencia_normativa='')
                        & ~Q(hash_fuente='')
                    )
                ),
                name='clasificador_vigente_fuente_oficial',
            ),
        ]
        indexes = [models.Index(fields=['tipo', 'gestion', 'vigente'])]

    def clean(self):
        super().clean()
        if not self.vigente:
            return
        errors = {}
        required = ('norma', 'codigo_fuente', 'procedencia_normativa', 'hash_fuente')
        for field in required:
            if not getattr(self, field):
                errors[field] = 'Una versión vigente requiere procedencia normativa completa.'
        if self.fecha_norma is None:
            errors['fecha_norma'] = 'Una versión vigente requiere fecha de la norma.'
        if self.clasificacion_fuente != self.FUENTE_OFICIAL:
            errors['clasificacion_fuente'] = 'Solo una fuente oficial puede declararse vigente.'
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        # Field/source validation runs here; race-safe uniqueness and the
        # official-source invariant remain enforced by PostgreSQL constraints.
        self.full_clean(validate_constraints=False)
        return super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.get_tipo_display()} {self.gestion} — {self.norma or "sin norma"}'


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


class ClasificadorVersionadoMixin(models.Model):
    TIPO_VERSION_CLASIFICADOR = None
    ANCHO_CODIGO_OFICIAL = None

    class Meta:
        abstract = True

    def clean(self):
        super().clean()
        if not self.version_clasificador_id:
            return
        errors = {}
        if self.version_clasificador.tipo != self.TIPO_VERSION_CLASIFICADOR:
            errors['version_clasificador'] = 'La versión no corresponde al tipo de clasificador.'
        if self.gestion != self.version_clasificador.gestion:
            errors['gestion'] = 'La gestión no coincide con la versión del clasificador.'
        if self.ANCHO_CODIGO_OFICIAL and (
            len(self.codigo) != self.ANCHO_CODIGO_OFICIAL or not self.codigo.isdigit()
        ):
            errors['codigo'] = (
                f'El código versionado debe tener {self.ANCHO_CODIGO_OFICIAL} dígitos.'
            )
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean(validate_constraints=False)
        return super().save(*args, **kwargs)


class ClasificadorInstitucional(CatalogoBase):
    class Meta:
        verbose_name = 'Clasificador institucional'
        verbose_name_plural = 'Clasificadores institucionales'


class RubroRecurso(CatalogoBase):
    class Meta:
        verbose_name = 'Rubro de recurso'
        verbose_name_plural = 'Rubros de recursos'


class ObjetoGasto(ClasificadorVersionadoMixin, CatalogoBase):
    TIPO_VERSION_CLASIFICADOR = VersionClasificador.TIPO_OBJETO_GASTO
    ANCHO_CODIGO_OFICIAL = 5
    NIVEL_GRUPO = 'grupo'
    NIVEL_SUBGRUPO = 'subgrupo'
    NIVEL_PARTIDA = 'partida'
    NIVEL_DETALLE = 'detalle'
    NIVEL_CHOICES = [
        (NIVEL_GRUPO, 'Grupo'),
        (NIVEL_SUBGRUPO, 'Subgrupo'),
        (NIVEL_PARTIDA, 'Partida'),
        (NIVEL_DETALLE, 'Detalle'),
    ]
    version_clasificador = models.ForeignKey(
        VersionClasificador,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='objetos_gasto',
    )
    padre = models.ForeignKey(
        'self',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='hijos',
    )
    nivel = models.CharField(max_length=20, choices=NIVEL_CHOICES, blank=True)

    class Meta:
        verbose_name = 'Objeto del gasto'
        verbose_name_plural = 'Objetos del gasto'
        constraints = [
            models.UniqueConstraint(
                fields=['codigo', 'version_clasificador'],
                condition=Q(version_clasificador__isnull=False),
                name='uniq_objeto_codigo_version',
            ),
        ]


class FuenteFinanciamiento(ClasificadorVersionadoMixin, CatalogoBase):
    TIPO_VERSION_CLASIFICADOR = VersionClasificador.TIPO_FUENTE_FINANCIAMIENTO
    ANCHO_CODIGO_OFICIAL = 2
    version_clasificador = models.ForeignKey(
        VersionClasificador,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='fuentes_financiamiento',
    )

    class Meta:
        verbose_name = 'Fuente de financiamiento'
        verbose_name_plural = 'Fuentes de financiamiento'
        constraints = [
            models.UniqueConstraint(
                fields=['codigo', 'version_clasificador'],
                condition=Q(version_clasificador__isnull=False),
                name='uniq_fuente_codigo_version',
            ),
        ]


class OrganismoFinanciador(ClasificadorVersionadoMixin, CatalogoBase):
    TIPO_VERSION_CLASIFICADOR = VersionClasificador.TIPO_ORGANISMO_FINANCIADOR
    ANCHO_CODIGO_OFICIAL = 3
    version_clasificador = models.ForeignKey(
        VersionClasificador,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='organismos_financiadores',
    )

    class Meta:
        verbose_name = 'Organismo financiador'
        verbose_name_plural = 'Organismos financiadores'
        constraints = [
            models.UniqueConstraint(
                fields=['codigo', 'version_clasificador'],
                condition=Q(version_clasificador__isnull=False),
                name='uniq_organismo_codigo_version',
            ),
        ]


class ClasificadorGeograficoPresupuestario(TimeStampedModel):
    """Geografía MEFP; intentionally independent from CGEO INE."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    version_clasificador = models.ForeignKey(
        VersionClasificador,
        on_delete=models.PROTECT,
        related_name='ubicaciones_geograficas_presupuestarias',
    )
    departamento = models.CharField(max_length=10)
    provincia = models.CharField(max_length=10)
    municipio = models.CharField(max_length=10)
    codigo_fuente = models.CharField(max_length=50)
    denominacion = models.CharField(max_length=300)
    procedencia_normativa = models.CharField(max_length=500)

    class Meta:
        verbose_name = 'Clasificador geográfico presupuestario'
        verbose_name_plural = 'Clasificadores geográficos presupuestarios'
        constraints = [
            models.UniqueConstraint(
                fields=['version_clasificador', 'departamento', 'provincia', 'municipio'],
                name='uniq_geo_presupuestario_version_codigo',
            ),
        ]
        indexes = [models.Index(fields=['version_clasificador', 'codigo_fuente'])]

    @property
    def codigo_compuesto(self):
        return '.'.join((self.departamento, self.provincia, self.municipio))


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
