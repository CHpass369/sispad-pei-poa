"""Catálogos oficiales versionados de codificación PAD-PEI-POA-POAU.

Todos los códigos oficiales (PGDESA, PDESA, sectores, CGEO, PAD) viven en
esta app. La cadena jerárquica PGDESA/PDESA/sector/resultado y los
lineamientos PAD se versionan por plan y gestión (VersionCatalogoPlan).
CGEO y EntidadCodificadora son catálogos estables: NO se versionan por
plan ni gestión. El código nunca es PK y nunca lo escribe el frontend.
"""
import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models
from django.db.models import Q

from apps.core.models import TimeStampedModel

# Constante de módulo para el estado vigente: el cuerpo de Meta no puede
# referenciar atributos de la clase en construcción, así que el partial
# unique de "una sola versión vigente por plan" usa esta fuente única.
ESTADO_CATALOGO_VIGENTE = 'vigente'


class VersionCatalogoPlan(TimeStampedModel):
    """Versión de los catálogos oficiales de un plan para una gestión.

    Una versión agrupa todos los catálogos (ejes, componentes, sectores,
    resultados, lineamientos PAD) aprobados por una norma. Solo puede
    existir una versión vigente por plan.
    """

    ESTADO_BORRADOR = 'borrador'
    ESTADO_VIGENTE = ESTADO_CATALOGO_VIGENTE
    ESTADO_CERRADO = 'cerrado'
    ESTADO_CHOICES = [
        (ESTADO_BORRADOR, 'Borrador'),
        (ESTADO_VIGENTE, 'Vigente'),
        (ESTADO_CERRADO, 'Cerrado'),
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
    plan = models.ForeignKey(
        'planificacion.Plan',
        on_delete=models.CASCADE,
        related_name='versiones_catalogo',
        verbose_name='Plan',
    )
    gestion = models.PositiveIntegerField(verbose_name='Gestión')
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default=ESTADO_BORRADOR,
        verbose_name='Estado',
    )
    norma_aprobacion = models.CharField(
        max_length=300,
        blank=True,
        verbose_name='Norma de aprobación',
    )
    clasificacion_fuente = models.CharField(
        max_length=20,
        choices=FUENTE_CHOICES,
        default=FUENTE_INCIERTA,
        verbose_name='Clasificación de la fuente',
    )
    procedencia_fuente = models.CharField(
        max_length=500,
        blank=True,
        default='',
        verbose_name='Procedencia de la fuente',
    )

    class Meta:
        verbose_name = 'Versión de catálogo de plan'
        verbose_name_plural = 'Versiones de catálogo de planes'
        ordering = ['plan', 'gestion']
        constraints = [
            models.UniqueConstraint(
                fields=['plan', 'gestion'],
                name='uniq_version_catalogo_plan_gestion',
            ),
            models.UniqueConstraint(
                fields=['plan'],
                condition=Q(estado=ESTADO_CATALOGO_VIGENTE),
                name='uniq_version_catalogo_vigente_por_plan',
            ),
        ]
        indexes = [
            models.Index(fields=['estado']),
            models.Index(fields=['gestion']),
        ]

    def __str__(self):
        return f'{self.plan.codigo} — {self.gestion} ({self.get_estado_display()})'


validador_codigo_2_digitos = RegexValidator(
    regex=r'^\d{2}$',
    message='El código debe tener exactamente 2 dígitos numéricos.',
)

# Validators de ancho del código CGEO (INE): el ancho depende del nivel
# territorial — departamento 2 dígitos (03), provincia 4 (0310) y
# municipio 6 (031001).
validador_cgeo_departamento = RegexValidator(
    regex=r'^\d{2}$',
    message='El código CGEO de departamento debe tener exactamente 2 dígitos numéricos.',
)
validador_cgeo_provincia = RegexValidator(
    regex=r'^\d{4}$',
    message='El código CGEO de provincia debe tener exactamente 4 dígitos numéricos.',
)
validador_cgeo_municipio = RegexValidator(
    regex=r'^\d{6}$',
    message='El código CGEO de municipio debe tener exactamente 6 dígitos numéricos.',
)
validador_codigo_4_digitos = RegexValidator(
    regex=r'^\d{4}$',
    message='El código de entidad debe tener exactamente 4 dígitos numéricos.',
)


class CatalogoSegmentoBase(TimeStampedModel):
    """Base abstracta para los catálogos jerárquicos versionados.

    Cada segmento del código oficial (EE, CC, SS, RS, LL) es una fila de
    catálogo: el código nunca es PK y siempre depende de una versión de
    catálogo aprobada por norma. Cada modelo concreto declara su FK
    ``version_catalogo`` con un related_name plural explícito en español.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    codigo = models.CharField(
        max_length=2,
        validators=[validador_codigo_2_digitos],
        verbose_name='Código',
    )
    denominacion = models.CharField(max_length=500, verbose_name='Denominación')
    activo = models.BooleanField(default=True, verbose_name='Activo')

    class Meta:
        abstract = True
        ordering = ['codigo']

    def __str__(self):
        return f'[{self.codigo}] {self.denominacion}'


class EjePGDESA(CatalogoSegmentoBase):
    """Eje del PGDESA (segmento EE, 2 dígitos). Raíz de la cadena nacional."""

    version_catalogo = models.ForeignKey(
        VersionCatalogoPlan,
        on_delete=models.CASCADE,
        related_name='ejes_pgdesa',
        verbose_name='Versión de catálogo',
    )

    class Meta(CatalogoSegmentoBase.Meta):
        verbose_name = 'Eje PGDESA'
        verbose_name_plural = 'Ejes PGDESA'
        constraints = [
            models.UniqueConstraint(
                fields=['codigo', 'version_catalogo'],
                name='uniq_eje_pgdesa_codigo_version',
            ),
        ]


class ComponentePDESA(CatalogoSegmentoBase):
    """Componente del PDESA (segmento CC, 2 dígitos), hijo de un eje PGDESA."""

    version_catalogo = models.ForeignKey(
        VersionCatalogoPlan,
        on_delete=models.CASCADE,
        related_name='componentes_pdesa',
        verbose_name='Versión de catálogo',
    )
    eje = models.ForeignKey(
        EjePGDESA,
        on_delete=models.CASCADE,
        related_name='componentes',
        verbose_name='Eje PGDESA',
    )

    class Meta(CatalogoSegmentoBase.Meta):
        verbose_name = 'Componente PDESA'
        verbose_name_plural = 'Componentes PDESA'
        constraints = [
            models.UniqueConstraint(
                fields=['eje', 'codigo', 'version_catalogo'],
                name='uniq_componente_pdesa_padre_codigo_version',
            ),
        ]
        indexes = [
            models.Index(fields=['eje', 'activo']),
        ]


class SectorEconomico(CatalogoSegmentoBase):
    """Sector económico (segmento SS, 2 dígitos), hijo de un componente PDESA."""

    version_catalogo = models.ForeignKey(
        VersionCatalogoPlan,
        on_delete=models.CASCADE,
        related_name='sectores_economicos',
        verbose_name='Versión de catálogo',
    )
    componente = models.ForeignKey(
        ComponentePDESA,
        on_delete=models.CASCADE,
        related_name='sectores',
        verbose_name='Componente PDESA',
    )

    class Meta(CatalogoSegmentoBase.Meta):
        verbose_name = 'Sector económico'
        verbose_name_plural = 'Sectores económicos'
        constraints = [
            models.UniqueConstraint(
                fields=['componente', 'codigo', 'version_catalogo'],
                name='uniq_sector_padre_codigo_version',
            ),
        ]
        indexes = [
            models.Index(fields=['componente', 'activo']),
        ]


class ResultadoSectorial(CatalogoSegmentoBase):
    """Resultado sectorial (segmento RS, 2 dígitos), hijo de un sector económico."""

    version_catalogo = models.ForeignKey(
        VersionCatalogoPlan,
        on_delete=models.CASCADE,
        related_name='resultados_sectoriales',
        verbose_name='Versión de catálogo',
    )
    sector = models.ForeignKey(
        SectorEconomico,
        on_delete=models.CASCADE,
        related_name='resultados',
        verbose_name='Sector económico',
    )

    class Meta(CatalogoSegmentoBase.Meta):
        verbose_name = 'Resultado sectorial'
        verbose_name_plural = 'Resultados sectoriales'
        constraints = [
            models.UniqueConstraint(
                fields=['sector', 'codigo', 'version_catalogo'],
                name='uniq_resultado_sectorial_padre_codigo_version',
            ),
        ]
        indexes = [
            models.Index(fields=['sector', 'activo']),
        ]


class EntidadTerritorialCGEO(TimeStampedModel):
    """Entidad territorial con código geográfico oficial INE por nivel.

    Reemplaza la segmentación DD.PP.MM: el código oficial usa UN segmento
    CGEO cuyo ancho depende del nivel — departamento 2 dígitos (03),
    provincia 4 (0310) y municipio 6 (031001). La jerarquía interna
    (departamento -> provincia -> municipio, vía FK padre) solo sirve para
    filtrar, NO segmenta el código. El segmento del código de articulación
    usa siempre el municipio (6 dígitos).
    """

    NIVEL_DEPARTAMENTO = 'departamento'
    NIVEL_PROVINCIA = 'provincia'
    NIVEL_MUNICIPIO = 'municipio'
    NIVEL_CHOICES = [
        (NIVEL_DEPARTAMENTO, 'Departamento'),
        (NIVEL_PROVINCIA, 'Provincia'),
        (NIVEL_MUNICIPIO, 'Municipio'),
    ]

    ESTADO_PROVISIONAL = 'provisional'
    ESTADO_OFICIAL = 'oficial'
    ESTADO_CHOICES = [
        (ESTADO_PROVISIONAL, 'Provisional'),
        (ESTADO_OFICIAL, 'Oficial'),
    ]

    VALIDADOR_CGEO_POR_NIVEL = {
        NIVEL_DEPARTAMENTO: validador_cgeo_departamento,
        NIVEL_PROVINCIA: validador_cgeo_provincia,
        NIVEL_MUNICIPIO: validador_cgeo_municipio,
    }

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    codigo = models.CharField(
        max_length=6,
        unique=True,
        verbose_name='Código CGEO (INE)',
    )
    nombre = models.CharField(max_length=200, verbose_name='Nombre')
    nivel = models.CharField(
        max_length=20,
        choices=NIVEL_CHOICES,
        verbose_name='Nivel',
    )
    padre = models.ForeignKey(
        'self',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='hijos',
        verbose_name='Entidad padre',
    )
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default=ESTADO_PROVISIONAL,
        verbose_name='Estado',
    )

    class Meta:
        verbose_name = 'Entidad territorial CGEO'
        verbose_name_plural = 'Entidades territoriales CGEO'
        ordering = ['codigo']
        indexes = [
            models.Index(fields=['nivel', 'estado']),
        ]

    def clean(self):
        super().clean()
        validador = self.VALIDADOR_CGEO_POR_NIVEL.get(self.nivel)
        if validador is None:
            # Nivel inválido: lo reporta la validación de choices del campo.
            return
        try:
            validador(self.codigo)
        except ValidationError as exc:
            raise ValidationError({'codigo': exc.messages}) from exc

    def __str__(self):
        return f'[{self.codigo}] {self.nombre} ({self.get_nivel_display()})'


class CodigoSegmentadoQuerySet(models.QuerySet):
    """Protect official codes from mutation through mass ORM operations."""

    MENSAJE_INMUTABLE = 'Los registros con código OFICIAL son inmutables.'
    MENSAJE_PROMOCION = 'Solo CodificadorService puede crear códigos OFICIALES.'

    def _contiene_oficial(self):
        return self.filter(estado_codigo='oficial').exists()

    def update(self, **kwargs):
        if self._contiene_oficial():
            raise ValidationError(self.MENSAJE_INMUTABLE)
        if (
            kwargs.get('estado_codigo') == 'oficial'
            or kwargs.get('codigo_completo_articulacion')
        ):
            raise ValidationError(self.MENSAJE_PROMOCION)
        return super().update(**kwargs)

    def delete(self):
        if self._contiene_oficial():
            raise ValidationError(self.MENSAJE_INMUTABLE)
        return super().delete()

    def bulk_update(self, objs, fields, batch_size=None):
        objetos = list(objs)
        ids = [obj.pk for obj in objetos if obj.pk]
        if (
            any(obj.estado_codigo == 'oficial' for obj in objetos)
            or self.model._base_manager.filter(
                pk__in=ids, estado_codigo='oficial',
            ).exists()
        ):
            raise ValidationError(self.MENSAJE_INMUTABLE)
        return super().bulk_update(objetos, fields, batch_size=batch_size)

    def bulk_create(self, objs, *args, **kwargs):
        objetos = list(objs)
        if kwargs.get('update_conflicts') or any(
            obj.estado_codigo == 'oficial'
            or bool(obj.codigo_completo_articulacion)
            for obj in objetos
        ):
            raise ValidationError(self.MENSAJE_PROMOCION)
        return super().bulk_create(objetos, *args, **kwargs)


class CodigoSegmentadoManager(models.Manager.from_queryset(
    CodigoSegmentadoQuerySet,
)):
    """Inherited manager for every concrete segmented-code model."""


class CodigoSegmentadoModel(TimeStampedModel):
    """Mixin abstracto de codificación oficial segmentada.

    Lo aplican los 8 modelos operativos de articulación (ResultadoPAD,
    ProductoPAD, ResultadoPEI, ProductoPEI, AccionPOA, OperacionPOAU,
    ActividadPOAU, TareaPOAU). Aporta el correlativo del nivel, el
    segmento propio (zfill según ``ANCHO_SEGMENTO``) y la trazabilidad
    del código fuente original (ej. ``SIM-2027-OP-01``).

    El ``codigo_completo_articulacion`` (16 segmentos) lo genera SOLO el
    backend: el CodificadorService lo implementa en T3. Aquí el campo
    queda persistido y ``editable=False`` para que ningún formulario lo
    escriba.
    """

    ESTADO_CODIGO_PROVISIONAL = 'provisional'
    ESTADO_CODIGO_OFICIAL = 'oficial'
    ESTADO_CODIGO_CHOICES = [
        (ESTADO_CODIGO_PROVISIONAL, 'Provisional'),
        (ESTADO_CODIGO_OFICIAL, 'Oficial'),
    ]

    # Cada modelo concreto declara el ancho de su segmento: 2 dígitos
    # (RT/PT/OE/RI/PI) o 3 dígitos (ACP/OP/ACT/TAR).
    ANCHO_SEGMENTO = None
    CAMPOS_CODIFICACION_ADICIONALES = ()
    CAMPOS_CODIFICACION = (
        'correlativo',
        'segmento',
        'codigo_fuente',
        'codigo_normalizado',
        'codigo_completo_articulacion',
        'articulacion_incompleta',
        'estado_codigo',
    )

    correlativo = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name='Correlativo del nivel',
    )
    segmento = models.CharField(
        max_length=6,
        blank=True,
        default='',
        verbose_name='Segmento del nivel',
    )
    codigo_fuente = models.CharField(
        max_length=100,
        blank=True,
        default='',
        verbose_name='Código fuente original',
    )
    codigo_normalizado = models.CharField(
        max_length=6,
        blank=True,
        default='',
        verbose_name='Código normalizado',
    )
    codigo_completo_articulacion = models.CharField(
        max_length=100,
        blank=True,
        default='',
        editable=False,
        verbose_name='Código completo de articulación',
    )
    articulacion_incompleta = models.BooleanField(
        default=True,
        editable=False,
        verbose_name='Articulación incompleta',
    )
    estado_codigo = models.CharField(
        max_length=20,
        choices=ESTADO_CODIGO_CHOICES,
        default=ESTADO_CODIGO_PROVISIONAL,
        verbose_name='Estado del código',
    )

    objects = CodigoSegmentadoManager()

    class Meta:
        abstract = True

    @classmethod
    def generar_segmento(cls, correlativo):
        """Return a positive correlativo padded to the exact level width.

        ``None`` is reserved for legacy rows that have not been coded yet.
        Every coded value must be a positive integer that fits completely in
        ``ANCHO_SEGMENTO``; booleans are rejected explicitly because Python
        otherwise treats them as integers.
        """
        if cls.ANCHO_SEGMENTO is None:
            raise NotImplementedError(
                f'{cls.__name__} debe declarar ANCHO_SEGMENTO (2 o 3).'
            )

        if correlativo is None:
            return ''

        valor_maximo = (10 ** cls.ANCHO_SEGMENTO) - 1
        if (
            isinstance(correlativo, bool)
            or not isinstance(correlativo, int)
            or not 1 <= correlativo <= valor_maximo
        ):
            raise ValidationError(
                f'El correlativo debe ser un entero entre 1 y {valor_maximo}.'
            )

        return str(correlativo).zfill(cls.ANCHO_SEGMENTO)

    def save(self, *args, **kwargs):
        """Reject every save after the persisted row becomes official."""
        permitir_promocion = getattr(self, '_permitir_promocion_oficial', False)
        if self.estado_codigo == self.ESTADO_CODIGO_OFICIAL and not self.pk:
            if not permitir_promocion:
                raise ValidationError(
                    'Solo CodificadorService puede promover un código a OFICIAL.'
                )

        if self.pk:
            anterior = type(self).objects.filter(pk=self.pk).first()
            if anterior is not None:
                if (
                    anterior.estado_codigo != self.ESTADO_CODIGO_OFICIAL
                    and self.estado_codigo == self.ESTADO_CODIGO_OFICIAL
                    and not permitir_promocion
                ):
                    raise ValidationError(
                        'Solo CodificadorService puede promover un código a OFICIAL.'
                    )
                if anterior.estado_codigo == self.ESTADO_CODIGO_OFICIAL:
                    raise ValidationError(
                        CodigoSegmentadoQuerySet.MENSAJE_INMUTABLE
                    )

        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        es_oficial = self.estado_codigo == self.ESTADO_CODIGO_OFICIAL
        if self.pk and not es_oficial:
            es_oficial = type(self).objects.filter(
                pk=self.pk,
                estado_codigo=self.ESTADO_CODIGO_OFICIAL,
            ).exists()
        if es_oficial:
            raise ValidationError(
                CodigoSegmentadoQuerySet.MENSAJE_INMUTABLE
            )
        return super().delete(*args, **kwargs)


# Niveles operativos de articulación que reciben código oficial segmentado.
# Fuente única para SecuenciaCodigo.nivel y HomologacionCodigo.tipo_entidad.
NIVEL_ARTICULACION_CHOICES = [
    ('resultado_pad', 'Resultado PAD'),
    ('producto_pad', 'Producto PAD'),
    ('resultado_pei', 'Resultado PEI'),
    ('producto_pei', 'Producto PEI'),
    ('accion_poa', 'Acción POA'),
    ('operacion_poau', 'Operación POAU'),
    ('actividad_poau', 'Actividad POAU'),
    ('tarea_poau', 'Tarea POAU'),
]


class EntidadCodificadora(TimeStampedModel):
    """Entidad pública que codifica (segmento ENTI, 4 dígitos).

    En esta base de datos solo se codifica 1312 (GAM Sacaba); el registro
    se siembra por data migration.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    codigo = models.CharField(
        max_length=4,
        unique=True,
        validators=[validador_codigo_4_digitos],
        verbose_name='Código',
    )
    denominacion = models.CharField(max_length=300, verbose_name='Denominación')
    activo = models.BooleanField(default=True, verbose_name='Activo')

    class Meta:
        verbose_name = 'Entidad codificadora'
        verbose_name_plural = 'Entidades codificadoras'
        ordering = ['codigo']

    def __str__(self):
        return f'[{self.codigo}] {self.denominacion}'


class LineamientoPAD(CatalogoSegmentoBase):
    """Lineamiento estratégico del PAD (segmento LL, 2 dígitos), consolidado.

    Catálogo versionado que reemplaza a `pad.LineamientoEstrategico` y
    `articulacion.LineamientoPAD` (ambos quedan deprecados hasta T5).
    """

    version_catalogo = models.ForeignKey(
        VersionCatalogoPlan,
        on_delete=models.CASCADE,
        related_name='lineamientos_pad',
        verbose_name='Versión de catálogo',
    )
    entidad_territorial = models.ForeignKey(
        EntidadTerritorialCGEO,
        on_delete=models.PROTECT,
        related_name='lineamientos_pad',
        verbose_name='Entidad territorial CGEO',
    )

    class Meta(CatalogoSegmentoBase.Meta):
        verbose_name = 'Lineamiento PAD'
        verbose_name_plural = 'Lineamientos PAD'
        constraints = [
            models.UniqueConstraint(
                fields=['entidad_territorial', 'codigo', 'version_catalogo'],
                name='uniq_lineamiento_pad_territorio_codigo_version',
            ),
        ]
        indexes = [
            models.Index(fields=['entidad_territorial', 'activo']),
        ]


class SecuenciaCodigo(TimeStampedModel):
    """Último correlativo emitido por clave (nivel, padre, gestión, entidad).

    Pensada para ``select_for_update()``: el CodificadorService (T3) toma
    el lock de la fila, incrementa ``ultimo_valor`` y confirma, así dos
    transacciones concurrentes jamás reciben el mismo correlativo. El
    correlativo reinicia por (padre, gestión, entidad). En niveles raíz
    ``padre_id`` es NULL y la unicidad se garantiza con
    ``nulls_distinct=False``.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nivel = models.CharField(
        max_length=30,
        choices=NIVEL_ARTICULACION_CHOICES,
        verbose_name='Nivel de articulación',
    )
    padre_id = models.UUIDField(
        null=True,
        blank=True,
        verbose_name='ID del registro padre',
    )
    gestion = models.PositiveIntegerField(verbose_name='Gestión')
    entidad = models.ForeignKey(
        EntidadCodificadora,
        on_delete=models.PROTECT,
        related_name='secuencias_codigo',
        verbose_name='Entidad codificadora',
    )
    ultimo_valor = models.PositiveIntegerField(
        default=0,
        verbose_name='Último correlativo emitido',
    )

    class Meta:
        verbose_name = 'Secuencia de código'
        verbose_name_plural = 'Secuencias de códigos'
        ordering = ['nivel', 'gestion']
        constraints = [
            models.UniqueConstraint(
                fields=['nivel', 'padre_id', 'gestion', 'entidad'],
                nulls_distinct=False,
                name='uniq_secuencia_codigo_clave',
            ),
        ]

    def __str__(self):
        return f'{self.nivel} G{self.gestion} → {self.ultimo_valor}'


class HomologacionCodigoQuerySet(models.QuerySet):
    """Reject every mutating operation against existing audit rows."""

    MENSAJE_APPEND_ONLY = (
        'Las homologaciones de código son append-only: '
        'no se pueden modificar ni eliminar.'
    )

    def update(self, **kwargs):
        raise ValidationError(self.MENSAJE_APPEND_ONLY)

    def delete(self):
        raise ValidationError(self.MENSAJE_APPEND_ONLY)

    def bulk_update(self, objs, fields, batch_size=None):
        raise ValidationError(self.MENSAJE_APPEND_ONLY)


class HomologacionCodigoManager(models.Manager.from_queryset(
    HomologacionCodigoQuerySet,
)):
    """Manager that exposes only append-safe mutation semantics."""


class HomologacionCodigo(TimeStampedModel):
    """Registro append-only de homologación de códigos.

    Cada vez que un código cambia (ej. ``SIM-2027-OP-01`` → código
    oficial de 16 segmentos) se inserta una fila con el respaldo
    documentario. Nunca se actualiza ni se borra: es la pista de
    auditoría del proceso de codificación.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tipo_entidad = models.CharField(
        max_length=30,
        choices=NIVEL_ARTICULACION_CHOICES,
        verbose_name='Tipo de entidad',
    )
    entidad_id = models.UUIDField(verbose_name='ID de la entidad homologada')
    codigo_anterior = models.CharField(
        max_length=100,
        verbose_name='Código anterior',
    )
    codigo_nuevo = models.CharField(
        max_length=100,
        verbose_name='Código nuevo',
    )
    motivo = models.TextField(verbose_name='Motivo')
    gestion = models.PositiveIntegerField(verbose_name='Gestión')
    fecha = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de homologación',
    )
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='homologaciones_codigo',
        verbose_name='Usuario',
    )
    documento_respaldo = models.CharField(
        max_length=300,
        blank=True,
        verbose_name='Documento de respaldo',
    )

    objects = HomologacionCodigoManager()

    class Meta:
        verbose_name = 'Homologación de código'
        verbose_name_plural = 'Homologaciones de códigos'
        ordering = ['-fecha']
        indexes = [
            models.Index(fields=['tipo_entidad', 'codigo_anterior']),
            models.Index(fields=['entidad_id']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['tipo_entidad', 'entidad_id', 'codigo_nuevo'],
                name='uniq_homologacion_entidad_codigo_nuevo',
            ),
        ]

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValidationError(
                'Las homologaciones de código son append-only: '
                'no se pueden modificar.'
            )
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError(
            'Las homologaciones de código son append-only: '
            'no se pueden eliminar.'
        )

    def __str__(self):
        return f'{self.tipo_entidad}: {self.codigo_anterior} → {self.codigo_nuevo}'
