import uuid
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models
from django.db.models import Q
from apps.core.models import TimeStampedModel, ActivableModel, VigenciaModel
from apps.gestion.models import GestionFiscal


class VersionClasificadorQuerySet(models.QuerySet):
    CAMPOS_SEMANTICOS = frozenset({
        'tipo', 'gestion', 'norma', 'fecha_norma', 'codigo_fuente',
        'procedencia_normativa', 'hash_fuente', 'clasificacion_fuente',
        'vigente',
    })

    def update(self, **kwargs):
        if self.CAMPOS_SEMANTICOS.intersection(kwargs):
            raise ValidationError(
                'Los campos semánticos de una versión requieren validación por instancia.'
            )
        return super().update(**kwargs)

    def bulk_update(self, objs, fields, batch_size=None):
        if self.CAMPOS_SEMANTICOS.intersection(fields):
            raise ValidationError(
                'Los campos semánticos de una versión no admiten bulk_update.'
            )
        return super().bulk_update(objs, fields, batch_size=batch_size)

    def bulk_create(self, objs, *args, **kwargs):
        objetos = list(objs)
        for objeto in objetos:
            objeto.full_clean()
        return super().bulk_create(objetos, *args, **kwargs)


class VersionClasificadorManager(models.Manager.from_queryset(
    VersionClasificadorQuerySet,
)):
    def vigente_para(self, tipo, gestion):
        """Fail closed: an absent explicit current version is an error."""
        # PIP-DB-003: gestion es FK; el año llega como int desde los callers.
        if not isinstance(gestion, GestionFiscal):
            return self.get(tipo=tipo, gestion__anio=gestion, vigente=True)
        return self.get(tipo=tipo, gestion=gestion, vigente=True)


class VersionClasificador(TimeStampedModel):
    TIPO_INSTITUCIONAL = 'institucional'
    TIPO_RUBRO_RECURSO = 'rubro_recurso'
    TIPO_OBJETO_GASTO = 'objeto_gasto'
    TIPO_FINALIDAD_FUNCION = 'finalidad_funcion'
    TIPO_FUENTE_FINANCIAMIENTO = 'fuente_financiamiento'
    TIPO_ORGANISMO_FINANCIADOR = 'organismo_financiador'
    TIPO_SECTOR_ECONOMICO = 'sector_economico'
    TIPO_CATEGORIA_PROGRAMATICA = 'categoria_programatica'
    TIPO_GEOGRAFICO_PRESUPUESTARIO = 'geografico_presupuestario'
    TIPO_CHOICES = [
        (TIPO_INSTITUCIONAL, 'Institucional'),
        (TIPO_RUBRO_RECURSO, 'Rubro de recurso'),
        (TIPO_OBJETO_GASTO, 'Objeto del gasto'),
        (TIPO_FINALIDAD_FUNCION, 'Finalidad/Función'),
        (TIPO_FUENTE_FINANCIAMIENTO, 'Fuente de financiamiento'),
        (TIPO_ORGANISMO_FINANCIADOR, 'Organismo financiador'),
        (TIPO_SECTOR_ECONOMICO, 'Sector económico'),
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
    gestion = models.ForeignKey(
        GestionFiscal, on_delete=models.PROTECT, db_column='gestion',
        related_name='+', verbose_name='Gestión fiscal',
    )
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
        db_table = 'catalogo_version_clasificador'
        ordering = ['tipo', '-gestion__anio', '-fecha_norma']
        constraints = [
            models.UniqueConstraint(
                fields=['tipo', 'gestion'],
                condition=Q(vigente=True),
                name='uniq_clasificador_vigente_tipo_gestion',
            ),
            models.CheckConstraint(
                condition=(
                    (Q(vigente=False) & ~Q(clasificacion_fuente='oficial'))
                    | (
                        Q(clasificacion_fuente='oficial')
                        & Q(norma__regex=r'.*\S.*')
                        & Q(fecha_norma__isnull=False)
                        & Q(codigo_fuente__regex=r'.*\S.*')
                        & Q(procedencia_normativa__regex=r'.*\S.*')
                        & Q(hash_fuente__regex=r'^[0-9a-f]{64}$')
                    )
                ),
                name='clasificador_vigente_fuente_oficial',
            ),
        ]
        indexes = [models.Index(fields=['tipo', 'gestion', 'vigente'])]

    def clean(self):
        super().clean()
        requiere_fuente_oficial = (
            self.vigente or self.clasificacion_fuente == self.FUENTE_OFICIAL
        )
        if not requiere_fuente_oficial:
            return
        errors = {}
        required = ('norma', 'codigo_fuente', 'procedencia_normativa', 'hash_fuente')
        for field in required:
            value = getattr(self, field)
            if not value or (isinstance(value, str) and not value.strip()):
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
    gestion = models.ForeignKey(
        GestionFiscal, on_delete=models.PROTECT, db_column='gestion',
        related_name='+', verbose_name='Gestión fiscal',
    )
    fuente_normativa = models.CharField(max_length=500, blank=True)
    metadatos_importacion = models.JSONField(null=True, blank=True)

    class Meta:
        abstract = True
        unique_together = [('codigo', 'gestion')]
        ordering = ['codigo', 'gestion__anio']

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

    def _campos_semanticos_masivos(self):
        return {'codigo', 'gestion', 'version_clasificador', 'version_clasificador_id'}

    def save(self, *args, **kwargs):
        self.full_clean(validate_constraints=False)
        return super().save(*args, **kwargs)


class ClasificadorVersionadoQuerySet(models.QuerySet):
    CAMPOS_SEMANTICOS = frozenset({
        'codigo', 'gestion', 'version_clasificador', 'version_clasificador_id',
        'padre', 'padre_id',
    })

    def update(self, **kwargs):
        if self.CAMPOS_SEMANTICOS.intersection(kwargs):
            raise ValidationError(
                'Las asociaciones versionadas no admiten actualización masiva.'
            )
        return super().update(**kwargs)

    def bulk_update(self, objs, fields, batch_size=None):
        if self.CAMPOS_SEMANTICOS.intersection(fields):
            raise ValidationError(
                'Las asociaciones versionadas no admiten bulk_update.'
            )
        return super().bulk_update(objs, fields, batch_size=batch_size)

    def bulk_create(self, objs, *args, **kwargs):
        objetos = list(objs)
        for objeto in objetos:
            objeto.full_clean()
        return super().bulk_create(objetos, *args, **kwargs)


class ClasificadorVersionadoManager(models.Manager.from_queryset(
    ClasificadorVersionadoQuerySet,
)):
    pass


ClasificadorVersionadoMixin.add_to_class(
    'objects', ClasificadorVersionadoManager(),
)


class ClasificadorInstitucional(ClasificadorVersionadoMixin, CatalogoBase):
    TIPO_VERSION_CLASIFICADOR = VersionClasificador.TIPO_INSTITUCIONAL
    # The MEFP institutional classifier uses variable-width numeric codes
    # (for example 6, 650, and 1312); do not impose a PIP-specific width.
    ANCHO_CODIGO_OFICIAL = None
    version_clasificador = models.ForeignKey(
        VersionClasificador,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='clasificadores_institucionales',
    )

    class Meta(CatalogoBase.Meta):
        db_table = 'catalogo_clasificador_institucional'
        verbose_name = 'Clasificador institucional'
        verbose_name_plural = 'Clasificadores institucionales'
        constraints = [
            models.UniqueConstraint(
                fields=['codigo', 'version_clasificador'],
                condition=Q(version_clasificador__isnull=False),
                name='uniq_institucional_codigo_version',
            ),
        ]


class RubroRecurso(ClasificadorVersionadoMixin, CatalogoBase):
    TIPO_VERSION_CLASIFICADOR = VersionClasificador.TIPO_RUBRO_RECURSO
    version_clasificador = models.ForeignKey(
        VersionClasificador,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='rubros_recurso',
    )

    class Meta(CatalogoBase.Meta):
        db_table = 'catalogo_rubro_recurso'
        verbose_name = 'Rubro de recurso'
        verbose_name_plural = 'Rubros de recursos'
        constraints = [
            models.UniqueConstraint(
                fields=['codigo', 'version_clasificador'],
                condition=Q(version_clasificador__isnull=False),
                name='uniq_rubro_codigo_version',
            ),
        ]


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

    class Meta(CatalogoBase.Meta):
        db_table = 'catalogo_objeto_gasto'
        verbose_name = 'Objeto del gasto'
        verbose_name_plural = 'Objetos del gasto'
        constraints = [
            models.UniqueConstraint(
                fields=['codigo', 'version_clasificador'],
                condition=Q(version_clasificador__isnull=False),
                name='uniq_objeto_codigo_version',
            ),
        ]

    def clean(self):
        super().clean()
        if not self.padre_id:
            return
        errors = {}
        if self.padre.gestion != self.gestion:
            errors['padre'] = 'El objeto padre debe pertenecer a la misma gestión.'
        if self.padre.version_clasificador_id != self.version_clasificador_id:
            errors['padre'] = 'El objeto padre debe compartir la versión del clasificador.'
        if errors:
            raise ValidationError(errors)


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

    class Meta(CatalogoBase.Meta):
        db_table = 'catalogo_fuente_financiamiento'
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

    class Meta(CatalogoBase.Meta):
        db_table = 'catalogo_organismo_financiador'
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
        db_table = 'catalogo_ubicacion_geografica_presupuestaria'
        verbose_name = 'Clasificador geográfico presupuestario'
        verbose_name_plural = 'Clasificadores geográficos presupuestarios'
        constraints = [
            models.UniqueConstraint(
                fields=['version_clasificador', 'departamento', 'provincia', 'municipio'],
                name='uniq_geo_presupuestario_version_codigo',
            ),
        ]
        indexes = [models.Index(fields=['version_clasificador', 'codigo_fuente'])]

    def clean(self):
        super().clean()
        if self.version_clasificador_id and self.version_clasificador.tipo != (
            VersionClasificador.TIPO_GEOGRAFICO_PRESUPUESTARIO
        ):
            raise ValidationError(
                {'version_clasificador': 'La versión no corresponde al tipo geográfico presupuestario.'}
            )

    def save(self, *args, **kwargs):
        self.full_clean(validate_constraints=False)
        return super().save(*args, **kwargs)

    @property
    def codigo_compuesto(self):
        return '.'.join((self.departamento, self.provincia, self.municipio))


class EntidadTransferencia(CatalogoBase):
    """Entidad otorgante o de transferencia"""
    class Meta(CatalogoBase.Meta):
        db_table = 'catalogo_entidad_transferencia'
        verbose_name = 'Entidad de transferencia'
        verbose_name_plural = 'Entidades de transferencia'


class FinalidadFuncion(ClasificadorVersionadoMixin, CatalogoBase):
    TIPO_VERSION_CLASIFICADOR = VersionClasificador.TIPO_FINALIDAD_FUNCION
    version_clasificador = models.ForeignKey(
        VersionClasificador,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='finalidades_funciones',
    )

    class Meta(CatalogoBase.Meta):
        db_table = 'catalogo_finalidad_funcion'
        verbose_name = 'Finalidad/Función'
        verbose_name_plural = 'Finalidades y funciones'
        constraints = [
            models.UniqueConstraint(
                fields=['codigo', 'version_clasificador'],
                condition=Q(version_clasificador__isnull=False),
                name='uniq_finalidad_codigo_version',
            ),
        ]


class UnidadMedida(CatalogoBase):
    class Meta(CatalogoBase.Meta):
        db_table = 'catalogo_unidad_medida'
        verbose_name = 'Unidad de medida'
        verbose_name_plural = 'Unidades de medida'


class TipoOperacion(CatalogoBase):
    class Meta(CatalogoBase.Meta):
        db_table = 'catalogo_tipo_operacion'
        verbose_name = 'Tipo de operación'
        verbose_name_plural = 'Tipos de operación'


class TipoProducto(CatalogoBase):
    class Meta(CatalogoBase.Meta):
        db_table = 'catalogo_tipo_producto'
        verbose_name = 'Tipo de producto'
        verbose_name_plural = 'Tipos de producto'


class TipoProyecto(CatalogoBase):
    class Meta(CatalogoBase.Meta):
        db_table = 'catalogo_tipo_proyecto'
        verbose_name = 'Tipo de proyecto'
        verbose_name_plural = 'Tipos de proyecto'


class TipoFinanciamiento(CatalogoBase):
    class Meta(CatalogoBase.Meta):
        db_table = 'catalogo_tipo_financiamiento'
        verbose_name = 'Tipo de financiamiento'
        verbose_name_plural = 'Tipos de financiamiento'


class VersionCatalogo(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nombre = models.CharField(max_length=200)
    gestion = models.ForeignKey(
        GestionFiscal, on_delete=models.PROTECT, db_column='gestion',
        related_name='+', verbose_name='Gestión fiscal',
    )
    archivo = models.FileField(upload_to='catalogos/', null=True, blank=True)
    aplicado = models.BooleanField(default=False)
    fecha_aplicacion = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'catalogo_version_catalogo'
        verbose_name = 'Versión de catálogo'
        verbose_name_plural = 'Versiones de catálogo'
        ordering = ['-gestion__anio', '-creado_en']

    creado_en = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.nombre} - {self.gestion}'


class SectorEconomicoPresupuestario(ClasificadorVersionadoMixin, CatalogoBase):
    """Clasificador presupuestario de sector económico del catálogo maestro.

    Independiente de ``codificacion.SectorEconomico`` (segmento SS del PAD):
    este clasificador tiene 3 niveles y ~406 ítems (R5 del mapeo). Su código
    es punteado (``1.1.1``) y la jerarquía se resuelve por ``parent_uuid``.
    """

    TIPO_VERSION_CLASIFICADOR = VersionClasificador.TIPO_SECTOR_ECONOMICO
    version_clasificador = models.ForeignKey(
        VersionClasificador,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='sectores_economicos',
    )
    padre = models.ForeignKey(
        'self',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='hijos',
        verbose_name='Padre',
    )
    nivel = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='Nivel',
        help_text='Profundidad derivada del código (1, 2 o 3).',
    )

    class Meta(CatalogoBase.Meta):
        verbose_name = 'Sector económico presupuestario'
        verbose_name_plural = 'Sectores económicos presupuestarios'
        ordering = ['codigo']
        constraints = [
            models.UniqueConstraint(
                fields=['codigo', 'version_clasificador'],
                condition=Q(version_clasificador__isnull=False),
                name='uniq_sector_economico_codigo_version',
            ),
        ]

    def clean(self):
        super().clean()
        if self.padre_id and self.padre.gestion != self.gestion:
            raise ValidationError(
                {'padre': 'El padre debe pertenecer a la misma gestión.'}
            )
        if self.padre_id and self.padre.version_clasificador_id != self.version_clasificador_id:
            raise ValidationError(
                {'padre': 'El padre debe compartir la versión del clasificador.'}
            )


class ValidacionPlataforma(TimeStampedModel):
    """Control parametrizado del motor de validaciones de articuladores.

    El catálogo maestro trae 9 validaciones (VAL-001..009) por módulo
    (POA/POAU/PRESUPUESTO/ARTICULACION/CODIFICACION/CRONOGRAMA/NORMATIVA).
    Hoy el motor de validaciones no tenía modelo: esta tabla lo parametriza.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    codigo = models.CharField(max_length=20, unique=True, verbose_name='Código')
    modulo = models.CharField(max_length=30, verbose_name='Módulo')
    control = models.CharField(max_length=100, verbose_name='Control')
    regla = models.TextField(blank=True, verbose_name='Regla')
    nivel = models.CharField(
        max_length=20, blank=True, default='ERROR', verbose_name='Nivel',
    )
    efecto = models.CharField(
        max_length=30, blank=True, default='BLOQUEA_ENVIO', verbose_name='Efecto',
    )
    activo = models.BooleanField(default=True, verbose_name='Activo')
    metadatos_importacion = models.JSONField(null=True, blank=True)

    class Meta:
        verbose_name = 'Validación de plataforma'
        verbose_name_plural = 'Validaciones de plataforma'
        ordering = ['modulo', 'codigo']

    def __str__(self):
        return f'[{self.codigo}] {self.modulo} — {self.control}'
