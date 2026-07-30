"""Catálogos oficiales versionados de codificación PAD-PEI-POA-POAU.

Todos los códigos oficiales (PGDESA, PDESA, sectores, CGEO, PAD) viven en
esta app, versionados por plan y gestión. El código nunca es PK y nunca lo
escribe el frontend.
"""
import uuid

from django.core.validators import RegexValidator
from django.db import models
from django.db.models import Q

from apps.core.models import TimeStampedModel


class VersionCatalogoPlan(TimeStampedModel):
    """Versión de los catálogos oficiales de un plan para una gestión.

    Una versión agrupa todos los catálogos (ejes, componentes, sectores,
    resultados, lineamientos PAD) aprobados por una norma. Solo puede
    existir una versión vigente por plan.
    """

    ESTADO_BORRADOR = 'borrador'
    ESTADO_VIGENTE = 'vigente'
    ESTADO_CERRADO = 'cerrado'
    ESTADO_CHOICES = [
        (ESTADO_BORRADOR, 'Borrador'),
        (ESTADO_VIGENTE, 'Vigente'),
        (ESTADO_CERRADO, 'Cerrado'),
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
                condition=Q(estado='vigente'),
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


class CatalogoSegmentoBase(TimeStampedModel):
    """Base abstracta para los catálogos jerárquicos versionados.

    Cada segmento del código oficial (EE, CC, SS, RS, LL) es una fila de
    catálogo: el código nunca es PK y siempre depende de una versión de
    catálogo aprobada por norma.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    codigo = models.CharField(
        max_length=2,
        validators=[validador_codigo_2_digitos],
        verbose_name='Código',
    )
    denominacion = models.CharField(max_length=500, verbose_name='Denominación')
    version_catalogo = models.ForeignKey(
        VersionCatalogoPlan,
        on_delete=models.CASCADE,
        related_name='%(class)ss',
        verbose_name='Versión de catálogo',
    )
    activo = models.BooleanField(default=True, verbose_name='Activo')

    class Meta:
        abstract = True
        ordering = ['codigo']

    def __str__(self):
        return f'[{self.codigo}] {self.denominacion}'


class EjePGDESA(CatalogoSegmentoBase):
    """Eje del PGDESA (segmento EE, 2 dígitos). Raíz de la cadena nacional."""

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
    """Entidad territorial con código geográfico oficial INE de 6 dígitos.

    Reemplaza la segmentación DD.PP.MM: el código oficial usa UN segmento
    CGEO(6). La jerarquía interna (departamento -> provincia -> municipio,
    vía FK padre) solo sirve para filtrar, NO segmenta el código.
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

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    codigo = models.CharField(
        max_length=6,
        unique=True,
        validators=[RegexValidator(
            regex=r'^\d{6}$',
            message='El código CGEO debe tener exactamente 6 dígitos numéricos.',
        )],
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

    def __str__(self):
        return f'[{self.codigo}] {self.nombre} ({self.get_nivel_display()})'


class EntidadCodificadora(TimeStampedModel):
    """Entidad pública que codifica (segmento ENTI, 4 dígitos).

    En esta base de datos solo se codifica 1312 (GAM Sacaba); el registro
    se siembra por data migration.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    codigo = models.CharField(
        max_length=4,
        unique=True,
        validators=[RegexValidator(
            regex=r'^\d{4}$',
            message='El código de entidad debe tener exactamente 4 dígitos numéricos.',
        )],
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
