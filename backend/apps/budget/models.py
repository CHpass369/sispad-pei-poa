"""Modelos del ciclo presupuestario SIS-POA (apps.budget).

Fase 2 — Techo Directivo: techo + versiones inmutables (patrón
`VersionInstrumento`: checksum SHA-256 + inmutabilidad), recursos por origen
(SIGEP/MUNICIPAL/SALDO/OTRO), gastos obligatorios y documentos de respaldo.

Fase 1 (gestión fiscal): no crea entidades de negocio nuevas — la entidad de
gestión es `apps.gestion.GestionFiscal`.

Los modelos heredan de `TimeStampedModel` (created_at/updated_at/created_by/
updated_by) y reutilizan los catálogos corporativos de `apps.catalogos` y la
estructura organizacional de `apps.organizacion`.
"""
import hashlib
import json

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from apps.core.models import TimeStampedModel


# ---------------------------------------------------------------------------
# Estados del techo directivo (la versión es la que transita)
# ---------------------------------------------------------------------------
class EstadosTecho:
    BORRADOR = 'BORRADOR'
    EN_REVISION = 'EN_REVISION'
    OBSERVADO = 'OBSERVADO'
    APROBADO = 'APROBADO'
    FIJADO = 'FIJADO'

    CHOICES = [
        (BORRADOR, 'Borrador'),
        (EN_REVISION, 'En revisión'),
        (OBSERVADO, 'Observado'),
        (APROBADO, 'Aprobado'),
        (FIJADO, 'Fijado'),
    ]

    # Transiciones válidas de la máquina de estados (BORRADOR → EN_REVISION →
    # APROBADO → FIJADO; EN_REVISION → OBSERVADO y OBSERVADO → EN_REVISION).
    TRANSICIONES = {
        BORRADOR: {EN_REVISION},
        EN_REVISION: {OBSERVADO, APROBADO},
        OBSERVADO: {EN_REVISION},
        APROBADO: {FIJADO},
        FIJADO: set(),
    }


class OrigenRecurso:
    SIGEP = 'SIGEP'
    MUNICIPAL = 'MUNICIPAL'
    SALDO = 'SALDO'
    OTRO = 'OTRO'

    CHOICES = [
        (SIGEP, 'SIGEP'),
        (MUNICIPAL, 'Recursos propios municipales'),
        (SALDO, 'Saldo de caja y bancos'),
        (OTRO, 'Otros'),
    ]


class TipoDocumento:
    REPORTE_SIGEP = 'REPORTE_SIGEP'
    NOTA_MEF = 'NOTA_MEF'
    RESOLUCION = 'RESOLUCION'
    INFORME = 'INFORME'
    PROYECCION_RECURSOS_PROPIOS = 'PROYECCION_RECURSOS_PROPIOS'
    OTRO = 'OTRO'

    CHOICES = [
        (REPORTE_SIGEP, 'Reporte SIGEP'),
        (NOTA_MEF, 'Nota MEF'),
        (RESOLUCION, 'Resolución'),
        (INFORME, 'Informe'),
        (PROYECCION_RECURSOS_PROPIOS, 'Proyección de recursos propios'),
        (OTRO, 'Otro'),
    ]


# ---------------------------------------------------------------------------
# Techo directivo
# ---------------------------------------------------------------------------
class DirectiveCeiling(TimeStampedModel):
    """Techo directivo de una gestión fiscal.

    El techo es el contenedor; las versiones (`DirectiveCeilingVersion`) son
    las que transitan por la máquina de estados y la versión fijada es
    inmutable (patrón `VersionInstrumento`). `version_actual` apunta al
    número de la versión vigente del techo.
    """

    gestion = models.OneToOneField(
        'gestion.GestionFiscal', on_delete=models.CASCADE,
        related_name='directive_ceiling',
        help_text='Gestión fiscal del techo (una por gestión).',
    )
    estado = models.CharField(
        max_length=20, choices=EstadosTecho.CHOICES,
        default=EstadosTecho.BORRADOR,
    )
    version_actual = models.PositiveIntegerField(
        default=0, help_text='Número de la versión vigente del techo.'
    )

    class Meta:
        verbose_name = 'Techo directivo'
        verbose_name_plural = 'Techos directivos'
        ordering = ['-created_at']

    def __str__(self):
        return f'Techo directivo {self.gestion.anio} ({self.estado})'


class DirectiveCeilingVersion(TimeStampedModel):
    """Versión de un techo directivo; inmutable al fijarse.

    Replica el patrón de `VersionInstrumento` (apps.planificacion.models_v2):
    `calcular_hash()` genera un SHA-256 sobre los datos semánticos (recursos y
    gastos obligatorios ordenados, montos Decimal→str) y `fijar()` congela la
    versión. `save()` rechaza modificaciones cuando `inmutable=True` (salvo el
    propio flujo de fijación, que persiste el primer cambio).
    """

    ceiling = models.ForeignKey(
        DirectiveCeiling, on_delete=models.CASCADE, related_name='versiones',
    )
    numero = models.PositiveIntegerField()
    estado = models.CharField(
        max_length=20, choices=EstadosTecho.CHOICES,
        default=EstadosTecho.BORRADOR,
    )
    hash = models.CharField(
        max_length=64, blank=True, default='',
        help_text='SHA-256 de los datos semánticos; se llena al fijar.',
    )
    fecha_fijacion = models.DateTimeField(null=True, blank=True)
    fijado_por = models.ForeignKey(
        'accounts.Usuario', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='techos_fijados',
    )
    observaciones = models.TextField(blank=True, default='')
    inmutable = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Versión de techo directivo'
        verbose_name_plural = 'Versiones de techo directivo'
        ordering = ['ceiling', 'numero']
        constraints = [
            models.UniqueConstraint(
                fields=['ceiling', 'numero'],
                name='uniq_techo_version_numero',
            ),
        ]

    def __str__(self):
        return f'{self.ceiling.gestion.anio} v{self.numero} ({self.estado})'

    # -- Checksum (patrón VersionInstrumento) ------------------------------

    def _datos_checksum(self):
        """Datos semánticos de la versión, deterministas y ordenados."""
        recursos = [
            (
                r.origen,
                r.rubro.codigo if r.rubro_id else '',
                r.fuente.codigo if r.fuente_id else '',
                r.organismo.codigo if r.organismo_id else '',
                r.entidad_otorgante.codigo if r.entidad_otorgante_id else '',
                r.concepto,
                str(r.monto),
            )
            for r in self.recursos.select_related(
                'rubro', 'fuente', 'organismo', 'entidad_otorgante',
            ).order_by(
                'origen', 'concepto', 'monto', 'rubro__codigo',
                'fuente__codigo', 'organismo__codigo',
                'entidad_otorgante__codigo', 'id',
            )
        ]
        gastos = [
            (
                g.da.codigo if g.da_id else '',
                g.ue.codigo if g.ue_id else '',
                g.programa,
                g.actividad,
                g.denominacion,
                g.fuente.codigo if g.fuente_id else '',
                g.organismo.codigo if g.organismo_id else '',
                g.objeto_gasto.codigo if g.objeto_gasto_id else '',
                g.entidad_transferencia,
                str(g.monto),
            )
            for g in self.gastos_obligatorios.select_related(
                'da', 'ue', 'fuente', 'organismo', 'objeto_gasto',
            ).order_by(
                'programa', 'actividad', 'denominacion', 'monto',
                'da__codigo', 'ue__codigo', 'fuente__codigo',
                'organismo__codigo', 'objeto_gasto__codigo',
                'entidad_transferencia', 'id',
            )
        ]
        return {'recursos': recursos, 'gastos_obligatorios': gastos}

    def calcular_hash(self):
        """SHA-256 de los datos semánticos de la versión."""
        payload = self._datos_checksum()
        return hashlib.sha256(
            json.dumps(payload, ensure_ascii=False, sort_keys=True)
            .encode('utf-8')
        ).hexdigest()

    def verificar_hash(self):
        return bool(self.hash) and self.hash == self.calcular_hash()

    # -- Fijación (inmutabilidad) -------------------------------------------

    def fijar(self, usuario, observaciones=''):
        """Fija la versión: estado FIJADO, inmutable, checksum, fecha y autor."""
        self.estado = EstadosTecho.FIJADO
        self.inmutable = True
        self.hash = self.calcular_hash()
        self.fecha_fijacion = timezone.now()
        self.fijado_por = usuario
        self.observaciones = observaciones or self.observaciones
        self.save(update_fields=[
            'estado', 'inmutable', 'hash', 'fecha_fijacion',
            'fijado_por', 'observaciones', 'updated_at',
        ])

    # -- Protección ----------------------------------------------------------

    def save(self, *args, **kwargs):
        if self.pk and not kwargs.get('force_insert'):
            original = DirectiveCeilingVersion.objects.get(pk=self.pk)
            if original.inmutable:
                raise ValidationError(
                    'No se puede modificar una versión de techo fijada '
                    '(inmutable).'
                )
        super().save(*args, **kwargs)


class CeilingResource(TimeStampedModel):
    """Recurso (ingreso) componente del techo directivo, por origen.

    `CheckConstraint` garantiza monto >= 0 en base de datos.
    """

    version = models.ForeignKey(
        DirectiveCeilingVersion, on_delete=models.CASCADE,
        related_name='recursos',
    )
    origen = models.CharField(max_length=20, choices=OrigenRecurso.CHOICES)
    rubro = models.ForeignKey(
        'catalogos.RubroRecurso', null=True, blank=True,
        on_delete=models.PROTECT, related_name='recursos_techo',
    )
    fuente = models.ForeignKey(
        'catalogos.FuenteFinanciamiento', null=True, blank=True,
        on_delete=models.PROTECT, related_name='recursos_techo',
    )
    organismo = models.ForeignKey(
        'catalogos.OrganismoFinanciador', null=True, blank=True,
        on_delete=models.PROTECT, related_name='recursos_techo',
    )
    entidad_otorgante = models.ForeignKey(
        'catalogos.EntidadTransferencia', null=True, blank=True,
        on_delete=models.PROTECT, related_name='recursos_techo',
    )
    concepto = models.CharField(max_length=300, blank=True, default='')
    monto = models.DecimalField(
        max_digits=18, decimal_places=2, verbose_name='Monto (Bs)'
    )
    documento = models.ForeignKey(
        'budget.BudgetDocument', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='recursos',
    )

    class Meta:
        verbose_name = 'Recurso del techo'
        verbose_name_plural = 'Recursos del techo'
        ordering = ['version', 'origen', 'concepto']
        constraints = [
            models.CheckConstraint(
                condition=models.Q(monto__gte=0),
                name='check_ceilingresource_monto_positivo',
            ),
        ]

    def __str__(self):
        return f'{self.get_origen_display()} {self.concepto}: {self.monto}'

    def clean(self):
        if self.version_id and self.version.inmutable:
            raise ValidationError(
                'No se puede modificar una versión de techo fijada (inmutable).'
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class MandatoryExpense(TimeStampedModel):
    """Gasto obligatorio que se descuenta del techo bruto.

    Programas/actividades con ceros iniciales preservados (VARCHAR), como en
    la codificación oficial. `CheckConstraint` garantiza monto >= 0.
    """

    version = models.ForeignKey(
        DirectiveCeilingVersion, on_delete=models.CASCADE,
        related_name='gastos_obligatorios',
    )
    da = models.ForeignKey(
        'organizacion.DireccionAdministrativa', null=True, blank=True,
        on_delete=models.PROTECT, related_name='gastos_obligatorios',
    )
    ue = models.ForeignKey(
        'organizacion.UnidadEjecutora', null=True, blank=True,
        on_delete=models.PROTECT, related_name='gastos_obligatorios',
    )
    programa = models.CharField(max_length=20, blank=True, default='')
    actividad = models.CharField(max_length=20, blank=True, default='')
    denominacion = models.CharField(max_length=500, blank=True, default='')
    fuente = models.ForeignKey(
        'catalogos.FuenteFinanciamiento', null=True, blank=True,
        on_delete=models.PROTECT, related_name='gastos_obligatorios',
    )
    organismo = models.ForeignKey(
        'catalogos.OrganismoFinanciador', null=True, blank=True,
        on_delete=models.PROTECT, related_name='gastos_obligatorios',
    )
    objeto_gasto = models.ForeignKey(
        'catalogos.ObjetoGasto', null=True, blank=True,
        on_delete=models.PROTECT, related_name='gastos_obligatorios',
    )
    entidad_transferencia = models.CharField(max_length=300, blank=True, default='')
    monto = models.DecimalField(
        max_digits=18, decimal_places=2, verbose_name='Monto (Bs)'
    )
    documento = models.ForeignKey(
        'budget.BudgetDocument', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='gastos_obligatorios',
    )

    class Meta:
        verbose_name = 'Gasto obligatorio'
        verbose_name_plural = 'Gastos obligatorios'
        ordering = ['version', 'programa', 'actividad', 'denominacion']
        constraints = [
            models.CheckConstraint(
                condition=models.Q(monto__gte=0),
                name='check_mandatoryexpense_monto_positivo',
            ),
        ]

    def __str__(self):
        return f'{self.denominacion}: {self.monto}'

    def clean(self):
        if self.version_id and self.version.inmutable:
            raise ValidationError(
                'No se puede modificar una versión de techo fijada (inmutable).'
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class BudgetDocument(TimeStampedModel):
    """Documento de respaldo del techo (reporte SIGEP, nota MEF, resolución…).

    El archivo se guarda con `FileField(upload_to='budget/')`, es decir en
    `MEDIA_ROOT/budget/` (backend/media/budget/ en desarrollo). El `sha256`
    se calcula en `save()` sobre el contenido subido (chunks). `storage_path`
    es una propiedad que expone la ruta almacenada por el FileField.
    """

    gestion = models.ForeignKey(
        'gestion.GestionFiscal', on_delete=models.CASCADE,
        related_name='documentos_budget',
    )
    tipo = models.CharField(
        max_length=40, choices=TipoDocumento.CHOICES,
        default=TipoDocumento.OTRO,
    )
    nombre = models.CharField(max_length=300)
    mime_type = models.CharField(max_length=120, blank=True, default='')
    size = models.BigIntegerField(default=0, verbose_name='Tamaño (bytes)')
    sha256 = models.CharField(max_length=64, blank=True, default='')
    fecha_documento = models.DateField(null=True, blank=True)
    archivo = models.FileField(upload_to='budget/')
    metadata_json = models.JSONField(default=dict, blank=True)

    class Meta:
        verbose_name = 'Documento de presupuesto'
        verbose_name_plural = 'Documentos de presupuesto'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['gestion']),
        ]

    def __str__(self):
        return self.nombre

    @property
    def storage_path(self):
        """Ruta del archivo dentro del almacenamiento (MEDIA_ROOT)."""
        return self.archivo.name

    def save(self, *args, **kwargs):
        if self.archivo and not self.sha256:
            digest = hashlib.sha256()
            for chunk in self.archivo.chunks():
                digest.update(chunk)
            self.sha256 = digest.hexdigest()
            self.size = self.archivo.size
        super().save(*args, **kwargs)


# ---------------------------------------------------------------------------
# Fase 4 - Distribución presupuestaria: versiones de distribución, aperturas
# programáticas con asignaciones normalizadas por FF/OF y reservas.
# ---------------------------------------------------------------------------
class TipoApertura:
    """Tipo de apertura. DETAIL es el único tipo por ahora; el importador de
    la Fase 5 agrega PROGRAM_HEADER/ACTIVITY_HEADER etc."""
    DETAIL = 'DETAIL'

    CHOICES = [
        (DETAIL, 'Detalle'),
    ]


class EstadoApertura:
    BORRADOR = 'BORRADOR'
    ACTIVA = 'ACTIVA'
    CERRADA = 'CERRADA'

    CHOICES = [
        (BORRADOR, 'Borrador'),
        (ACTIVA, 'Activa'),
        (CERRADA, 'Cerrada'),
    ]


class TipoReserva:
    """Tipo de reserva. DISTRITAL: reserva para el reparto territorial
    (Fase 6). DISTRIBUCION: reserva global de la distribución. OTRA: otras."""
    DISTRITAL = 'DISTRITAL'
    DISTRIBUCION = 'DISTRIBUCION'
    OTRA = 'OTRA'

    CHOICES = [
        (DISTRITAL, 'Distrital'),
        (DISTRIBUCION, 'Distribución'),
        (OTRA, 'Otra'),
    ]


class EstadoReserva:
    ACTIVA = 'ACTIVA'
    LIBERADA = 'LIBERADA'

    CHOICES = [
        (ACTIVA, 'Activa'),
        (LIBERADA, 'Liberada'),
    ]


class DistributionVersion(TimeStampedModel):
    """Versión de la distribución presupuestaria de una gestión.

    Replica el patrón de `DirectiveCeilingVersion`/`VersionInstrumento`:
    la versión transita por los estados `EstadosTecho` (BORRADOR →
    EN_REVISION → APROBADO → FIJADO, con OBSERVADO) y al fijarse queda
    inmutable con checksum SHA-256. La distribución activa es la versión
    no fijada de mayor número; si no existe se crea la versión 1 al primer
    uso y, si la última está FIJADA, se exige un ajuste explícito (Fase 7).
    La fijación valida Σfuente = techo − reservas y el checksum lo calcula
    `services.checksum_distribucion` (única implementación; Fase 7).
    """

    gestion = models.ForeignKey(
        'gestion.GestionFiscal', on_delete=models.CASCADE,
        related_name='versiones_distribucion',
        help_text='Gestión fiscal de la distribución.',
    )
    numero = models.PositiveIntegerField(help_text='Número de versión.')
    estado = models.CharField(
        max_length=20, choices=EstadosTecho.CHOICES,
        default=EstadosTecho.BORRADOR,
    )
    hash = models.CharField(
        max_length=64, blank=True, default='',
        help_text='SHA-256 de los datos semánticos; se llena al fijar (Fase 7).',
    )
    fecha_fijacion = models.DateTimeField(null=True, blank=True)
    fijado_por = models.ForeignKey(
        'accounts.Usuario', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='distribuciones_fijadas',
    )
    observaciones = models.TextField(blank=True, default='')
    inmutable = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Versión de distribución'
        verbose_name_plural = 'Versiones de distribución'
        ordering = ['gestion', 'numero']
        constraints = [
            models.UniqueConstraint(
                fields=['gestion', 'numero'],
                name='uniq_distribution_version_numero',
            ),
        ]

    def __str__(self):
        return f'Distribución {self.gestion.anio} v{self.numero} ({self.estado})'

    # -- Checksum (patrón VersionInstrumento) ------------------------------

    def calcular_hash(self):
        """SHA-256 de los datos semánticos de la versión (Fase 7).

        Delega en `services.checksum_distribucion` (única implementación):
        (fuente, organismo, monto) de las asignaciones de las aperturas
        ACTIVAS de la versión + reservas de la versión, ordenadas de forma
        determinista.
        """
        from .services import checksum_distribucion
        return checksum_distribucion(self)

    def verificar_hash(self):
        return bool(self.hash) and self.hash == self.calcular_hash()

    # -- Fijación (inmutabilidad; Fase 7) -----------------------------------

    def fijar(self, usuario, observaciones=''):
        """Fija la versión: estado FIJADO, inmutable, checksum, fecha y autor."""
        self.estado = EstadosTecho.FIJADO
        self.inmutable = True
        self.hash = self.calcular_hash()
        self.fecha_fijacion = timezone.now()
        self.fijado_por = usuario
        self.observaciones = observaciones or self.observaciones
        self.save(update_fields=[
            'estado', 'inmutable', 'hash', 'fecha_fijacion',
            'fijado_por', 'observaciones', 'updated_at',
        ])

    # -- Protección ----------------------------------------------------------

    def save(self, *args, **kwargs):
        if self.pk and not kwargs.get('force_insert'):
            original = DistributionVersion.objects.get(pk=self.pk)
            if original.inmutable:
                raise ValidationError(
                    'No se puede modificar una versión de distribución '
                    'fijada (inmutable).'
                )
        super().save(*args, **kwargs)


class Allocation(TimeStampedModel):
    """Apertura programática de la distribución (por gestión).

    Referencia la categoría programática del ciclo (`budget.ProgrammaticCategory`)
    y las dimensiones organizacionales/territoriales. Los montos viven
    normalizados por FF/OF en `AllocationSource` — nunca columnas monto_ct/
    monto_re. Los códigos SISIN/proyecto/actividad son VARCHAR (ceros
    iniciales preservados).
    """

    gestion = models.ForeignKey(
        'gestion.GestionFiscal', on_delete=models.CASCADE,
        related_name='aperturas_presupuestarias',
    )
    version = models.ForeignKey(
        DistributionVersion, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='aperturas',
        help_text='Versión de distribución activa al momento de la apertura.',
    )
    unidad_organizacional = models.ForeignKey(
        'organizacion.UnidadOrganizacional', null=True, blank=True,
        on_delete=models.PROTECT, related_name='aperturas_presupuestarias',
    )
    distrito = models.ForeignKey(
        'territorio.Distrito', null=True, blank=True,
        on_delete=models.PROTECT, related_name='aperturas_presupuestarias',
    )
    da = models.ForeignKey(
        'organizacion.DireccionAdministrativa', null=True, blank=True,
        on_delete=models.PROTECT, related_name='aperturas_presupuestarias',
    )
    ue = models.ForeignKey(
        'organizacion.UnidadEjecutora', null=True, blank=True,
        on_delete=models.PROTECT, related_name='aperturas_presupuestarias',
    )
    categoria = models.ForeignKey(
        'budget.ProgrammaticCategory', null=True, blank=True,
        on_delete=models.PROTECT, related_name='aperturas',
        help_text='Categoría programática del ciclo.',
    )
    proyecto_codigo = models.CharField(max_length=20, blank=True, default='')
    codigo_sisin = models.CharField(
        max_length=20, blank=True, default='',
        help_text='Código SISIN (VARCHAR, ceros iniciales preservados).',
    )
    actividad_codigo = models.CharField(max_length=20, blank=True, default='')
    denominacion = models.CharField(max_length=300)
    tipo_apertura = models.CharField(
        max_length=20, choices=TipoApertura.CHOICES,
        default=TipoApertura.DETAIL,
    )
    estado = models.CharField(
        max_length=20, choices=EstadoApertura.CHOICES,
        default=EstadoApertura.ACTIVA,
    )
    orden = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = 'Apertura programática'
        verbose_name_plural = 'Aperturas programáticas'
        ordering = ['gestion', 'orden', 'id']
        indexes = [
            models.Index(fields=['gestion', 'version']),
            models.Index(fields=['gestion', 'categoria']),
            models.Index(fields=['gestion', 'distrito']),
        ]

    def __str__(self):
        return f'{self.codigo_sisin or "-"} - {self.denominacion}'

    @property
    def total(self):
        """Total de la apertura = suma de sus fuentes (agregación, nunca fila)."""
        total = self.fuentes.aggregate(models.Sum('monto'))['monto__sum']
        return total if total is not None else 0


class AllocationSource(TimeStampedModel):
    """Asignación normalizada de una apertura por FF/OF (nunca columnas).

    `UniqueConstraint(nulls_distinct=False)` garantiza una fila por
    (allocation, fuente, organismo) incluso cuando alguno es NULL.
    """

    allocation = models.ForeignKey(
        Allocation, on_delete=models.CASCADE, related_name='fuentes',
    )
    fuente = models.ForeignKey(
        'catalogos.FuenteFinanciamiento', null=True, blank=True,
        on_delete=models.PROTECT, related_name='allocation_sources',
    )
    organismo = models.ForeignKey(
        'catalogos.OrganismoFinanciador', null=True, blank=True,
        on_delete=models.PROTECT, related_name='allocation_sources',
    )
    monto = models.DecimalField(
        max_digits=18, decimal_places=2, verbose_name='Monto (Bs)'
    )

    class Meta:
        verbose_name = 'Asignación de apertura'
        verbose_name_plural = 'Asignaciones de apertura'
        ordering = ['allocation', 'fuente', 'organismo']
        constraints = [
            models.CheckConstraint(
                condition=models.Q(monto__gte=0),
                name='check_allocationsource_monto_positivo',
            ),
            models.UniqueConstraint(
                fields=['allocation', 'fuente', 'organismo'],
                name='uniq_allocation_fuente_organismo',
                nulls_distinct=False,
            ),
        ]

    def __str__(self):
        return f'{self.fuente.codigo if self.fuente_id else "-"}: {self.monto}'


class Reserve(TimeStampedModel):
    """Reserva presupuestaria sobre una fuente (decrece el disponible).

    Las reservas ACTIVAS restan del disponible por fuente; liberarlas lo
    devuelve. `CheckConstraint` garantiza monto >= 0 en base de datos.
    """

    gestion = models.ForeignKey(
        'gestion.GestionFiscal', on_delete=models.CASCADE,
        related_name='reservas_presupuestarias',
    )
    version = models.ForeignKey(
        DistributionVersion, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='reservas',
    )
    fuente = models.ForeignKey(
        'catalogos.FuenteFinanciamiento', null=True, blank=True,
        on_delete=models.PROTECT, related_name='reservas_por_fuente',
    )
    organismo = models.ForeignKey(
        'catalogos.OrganismoFinanciador', null=True, blank=True,
        on_delete=models.PROTECT, related_name='reservas_por_organismo',
    )
    tipo = models.CharField(
        max_length=20, choices=TipoReserva.CHOICES,
        default=TipoReserva.OTRA,
    )
    monto = models.DecimalField(
        max_digits=18, decimal_places=2, verbose_name='Monto (Bs)'
    )
    motivo = models.TextField(blank=True, default='')
    estado = models.CharField(
        max_length=20, choices=EstadoReserva.CHOICES,
        default=EstadoReserva.ACTIVA,
    )

    class Meta:
        verbose_name = 'Reserva presupuestaria'
        verbose_name_plural = 'Reservas presupuestarias'
        ordering = ['gestion', '-created_at']
        constraints = [
            models.CheckConstraint(
                condition=models.Q(monto__gte=0),
                name='check_reserve_monto_positivo',
            ),
        ]
        indexes = [
            models.Index(fields=['gestion', 'estado']),
            models.Index(fields=['gestion', 'version']),
        ]

    def __str__(self):
        return f'Reserva {self.get_tipo_display()} {self.monto}'


# ---------------------------------------------------------------------------
# Fase 3 - CategorAas programAticas del ciclo (jeraquAa PROGRAMA/SUBPROGRAMA/
# PROYECTO/ACTIVIDAD por gestiA3n). CAtAlogo propio del ciclo presupuestario;
# los niveles no son obligatorios en todas las categorAas.
# ---------------------------------------------------------------------------
class NivelCategoria:
    PROGRAMA = 'PROGRAMA'
    SUBPROGRAMA = 'SUBPROGRAMA'
    PROYECTO = 'PROYECTO'
    ACTIVIDAD = 'ACTIVIDAD'

    CHOICES = [
        (PROGRAMA, 'Programa'),
        (SUBPROGRAMA, 'Subprograma'),
        (PROYECTO, 'Proyecto'),
        (ACTIVIDAD, 'Actividad'),
    ]


class EstadoCategoria:
    ACTIVA = 'ACTIVA'
    INACTIVA = 'INACTIVA'

    CHOICES = [
        (ACTIVA, 'Activa'),
        (INACTIVA, 'Inactiva'),
    ]


class ProgrammaticCategory(TimeStampedModel):
    """CategorAa programAtica del ciclo presupuestario (por gestiA3n).

    JerarquAa flexible: PROGRAMA -> SUBPROGRAMA -> PROYECTO -> ACTIVIDAD.
    Los cA3digos se almacenan como VARCHAR (ceros iniciales preservados,
    cA3digos compuestos); una apertura no puede usar una categorAa inexistente
    (la FK lo garantiza).
    """

    gestion = models.ForeignKey(
        'gestion.GestionFiscal', on_delete=models.CASCADE,
        related_name='categorias_programaticas',
    )
    codigo = models.CharField(max_length=20)
    denominacion = models.CharField(max_length=300)
    nivel = models.CharField(
        max_length=20, choices=NivelCategoria.CHOICES,
        default=NivelCategoria.PROGRAMA,
    )
    parent = models.ForeignKey(
        'self', on_delete=models.CASCADE, null=True, blank=True,
        related_name='hijos',
    )
    vigencia_desde = models.DateField(null=True, blank=True)
    vigencia_hasta = models.DateField(null=True, blank=True)
    estado = models.CharField(
        max_length=20, choices=EstadoCategoria.CHOICES,
        default=EstadoCategoria.ACTIVA,
    )
    origen = models.CharField(max_length=40, blank=True, default='')
    normativa = models.CharField(max_length=120, blank=True, default='')
    observaciones = models.TextField(blank=True, default='')

    class Meta:
        verbose_name = 'CategorAa programAtica'
        verbose_name_plural = 'CategorAas programAticas'
        ordering = ['gestion', 'nivel', 'codigo']
        constraints = [
            models.UniqueConstraint(
                fields=['gestion', 'codigo'],
                name='budget_categoria_gestion_codigo_uniq',
            ),
        ]
        indexes = [
            models.Index(fields=['gestion', 'parent']),
        ]

    def __str__(self):
        return f'{self.codigo} - {self.denominacion}'

    def clean(self):
        from django.core.exceptions import ValidationError as VE
        if self.parent and self.parent.gestion_id != self.gestion_id:
            raise VE({'parent': 'La categorAa padre debe pertenecer a la misma gestiA3n.'})
        if self.parent and self.parent.nivel == self.nivel:
            raise VE({'parent': 'El nivel padre no puede ser igual al nivel de la categorAa.'})
        niveles = [NivelCategoria.PROGRAMA, NivelCategoria.SUBPROGRAMA,
                   NivelCategoria.PROYECTO, NivelCategoria.ACTIVIDAD]
        if self.parent and niveles.index(self.nivel) <= niveles.index(self.parent.nivel):
            raise VE({'nivel': 'El nivel debe ser mAs profundo que el de la categorAa padre.'})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


# ---------------------------------------------------------------------------
# Fase 5 - Importador Excel: staging de planillas (GASTOS historico/actual)
# ---------------------------------------------------------------------------
class EstadoImportacion:
    """Estados del staging de una importacion."""
    STAGING = 'STAGING'
    VALIDADO = 'VALIDADO'
    CORREGIDO = 'CORREGIDO'
    APLICADO = 'APLICADO'
    RECHAZADO = 'RECHAZADO'

    CHOICES = [
        (STAGING, 'En staging (sin validar)'),
        (VALIDADO, 'Validado (listo para aplicar)'),
        (CORREGIDO, 'Corregido'),
        (APLICADO, 'Aplicado'),
        (RECHAZADO, 'Rechazado'),
    ]


class PerfilImportacion:
    """Perfiles de planilla: definen columnas esperadas y el mapeo por defecto."""
    SISPOA_GASTOS_HISTORICO = 'SISPOA_GASTOS_HISTORICO'
    SISPOA_GASTOS_ACTUAL = 'SISPOA_GASTOS_ACTUAL'
    OTRO = 'OTRO'

    CHOICES = [
        (SISPOA_GASTOS_HISTORICO, 'GASTOS histórico (estructura oficial)'),
        (SISPOA_GASTOS_ACTUAL, 'GASTOS actual (planilla vigente)'),
        (OTRO, 'Otro'),
    ]


class ClasificacionFila:
    """Clasificacion de filas de la planilla (columna V/tipo)."""
    PROGRAM_HEADER = 'PROGRAM_HEADER'
    SUBPROGRAM_HEADER = 'SUBPROGRAM_HEADER'
    DETAIL = 'DETAIL'
    SUBTOTAL = 'SUBTOTAL'
    TOTAL = 'TOTAL'
    EMPTY = 'EMPTY'
    UNKNOWN = 'UNKNOWN'

    CHOICES = [
        (PROGRAM_HEADER, 'Encabezado de programa (P)'),
        (SUBPROGRAM_HEADER, 'Encabezado de subprograma (SP)'),
        (DETAIL, 'Fila de detalle'),
        (SUBTOTAL, 'Subtotal (TS)'),
        (TOTAL, 'Total (T)'),
        (EMPTY, 'Fila vacía'),
        (UNKNOWN, 'No clasificada'),
    ]


class EstadoDetalle:
    PENDIENTE = 'PENDIENTE'
    VALIDO = 'VALIDO'
    ERROR = 'ERROR'

    CHOICES = [
        (PENDIENTE, 'Pendiente'),
        (VALIDO, 'Válido'),
        (ERROR, 'Con errores'),
    ]


class SeveridadError:
    INFO = 'INFO'
    WARNING = 'WARNING'
    ERROR = 'ERROR'
    CRITICAL = 'CRITICAL'

    CHOICES = [
        (INFO, 'Info'),
        (WARNING, 'Advertencia'),
        (ERROR, 'Error'),
        (CRITICAL, 'Crítico'),
    ]


class AccionError:
    """Accion sugerida/ejecutada para resolver el error."""
    REEMPLAZAR = 'REEMPLAZAR'
    NORMALIZAR = 'NORMALIZAR'
    ASIGNAR = 'ASIGNAR'
    IGNORAR = 'IGNORAR'
    NINGUNA = 'NINGUNA'

    CHOICES = [
        (REEMPLAZAR, 'Reemplazar valor'),
        (NORMALIZAR, 'Normalizar'),
        (ASIGNAR, 'Asignar'),
        (IGNORAR, 'Ignorar'),
        (NINGUNA, 'Ninguna'),
    ]


class BudgetImport(TimeStampedModel):
    """Importacion de planilla presupuestaria en staging (Fase 5).

    La planilla se sube, se parsea a `ImportDetalle` (datos normalizados) y
    nunca se aplica directo: primero se valida (`validar_importacion`) y solo
    con errores resueltos se aplica (`aplicar_importacion`), que crea
    aperturas BORRADOR. `mapeo_json` guarda el mapeo columna->campo y el
    mapeo de fuentes por columna de monto (configurable por el usuario).
    """

    gestion = models.ForeignKey(
        'gestion.GestionFiscal', on_delete=models.CASCADE,
        related_name='importaciones_budget',
        help_text='Gestión fiscal a la que se importan las aperturas.',
    )
    perfil = models.CharField(
        max_length=40, choices=PerfilImportacion.CHOICES,
        default=PerfilImportacion.SISPOA_GASTOS_ACTUAL,
    )
    filename = models.CharField(max_length=300, blank=True, default='')
    mime_type = models.CharField(max_length=120, blank=True, default='')
    size = models.BigIntegerField(default=0, verbose_name='Tamaño (bytes)')
    sha256 = models.CharField(max_length=64, blank=True, default='')
    hoja_seleccionada = models.CharField(max_length=200, blank=True, default='')
    mapeo_json = models.JSONField(default=dict, blank=True)
    estado = models.CharField(
        max_length=20, choices=EstadoImportacion.CHOICES,
        default=EstadoImportacion.STAGING,
    )
    tipo_importacion = models.CharField(
        max_length=20, default='GASTOS',
        help_text='Tipo de contenido de la planilla (GASTOS por ahora).',
    )
    archivo = models.FileField(upload_to='budget/imports/')
    creado_por = models.ForeignKey(
        'accounts.Usuario', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='importaciones_budget',
    )

    class Meta:
        verbose_name = 'Importación de planilla'
        verbose_name_plural = 'Importaciones de planilla'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['gestion']),
        ]

    def __str__(self):
        return f'Import {self.filename or self.id} ({self.gestion.anio})'

    @property
    def storage_path(self):
        return self.archivo.name if self.archivo else ''

    def save(self, *args, **kwargs):
        if self.archivo and not self.sha256:
            digest = hashlib.sha256()
            for chunk in self.archivo.chunks():
                digest.update(chunk)
            self.sha256 = digest.hexdigest()
            self.size = self.archivo.size
        super().save(*args, **kwargs)


class ImportDetalle(TimeStampedModel):
    """Fila parseada de la planilla (solo candidatas: DETAIL/SUBTOTAL/TOTAL).

    `datos_json` guarda los campos normalizados (unidad, distrito, da, ue,
    programa, subprograma, sisin, actividad, denominacion, saldo, ct, re,
    ore, idh, tgn, total) + `_raw` (valores/tipos/formato originales) para
    re-validar sin releer el archivo.
    """

    importacion = models.ForeignKey(
        BudgetImport, on_delete=models.CASCADE, related_name='detalles',
    )
    fila = models.PositiveIntegerField(
        help_text='Número de fila real en la hoja (1-based).'
    )
    clasificacion = models.CharField(
        max_length=20, choices=ClasificacionFila.CHOICES,
        default=ClasificacionFila.DETAIL,
    )
    datos_json = models.JSONField(default=dict, blank=True)
    estado = models.CharField(
        max_length=20, choices=EstadoDetalle.CHOICES,
        default=EstadoDetalle.PENDIENTE,
    )
    errores_json = models.JSONField(default=list, blank=True)

    class Meta:
        verbose_name = 'Detalle de importación'
        verbose_name_plural = 'Detalles de importación'
        ordering = ['importacion', 'fila']
        indexes = [
            models.Index(fields=['importacion', 'estado']),
        ]

    def __str__(self):
        return f'{self.importacion_id} fila {self.fila} ({self.clasificacion})'


# ---------------------------------------------------------------------------
# Fase 6 - Distribución territorial: reparto de bolsas entre distritos
# (MANUAL/MONTO_FIJO/PORCENTAJE/POBLACION/FORMULA) materializado como reservas
# DISTRITALES (no crea aperturas artificiales).
# ---------------------------------------------------------------------------
class MetodoDistribucion:
    MANUAL = 'MANUAL'
    MONTO_FIJO = 'MONTO_FIJO'
    PORCENTAJE = 'PORCENTAJE'
    POBLACION = 'POBLACION'
    FORMULA = 'FORMULA'

    CHOICES = [
        (MANUAL, 'Manual'),
        (MONTO_FIJO, 'Monto fijo'),
        (PORCENTAJE, 'Porcentaje'),
        (POBLACION, 'Población'),
        (FORMULA, 'Fórmula'),
    ]


class EstadoDistribucionTerritorial:
    BORRADOR = 'BORRADOR'
    CALCULADA = 'CALCULADA'
    APLICADA = 'APLICADA'

    CHOICES = [
        (BORRADOR, 'Borrador'),
        (CALCULADA, 'Calculada'),
        (APLICADA, 'Aplicada'),
    ]


class TerritorialDistribution(TimeStampedModel):
    """Reparto de una bolsa presupuestaria entre distritos (Fase 6).

    La distribución transita BORRADOR → CALCULADA → APLICADA. `calcular`
    calcula los montos por distrito (`TerritorialAllocation`) con ajuste de
    redondeo exacto (SUM(monto_final) = bolsa_total); `aplicar` materializa
    el reparto como reservas DISTRITALES sobre la fuente (decrece el
    disponible) y `liberar` las devuelve. `version` es la versión de
    distribución activa al aplicar (puede ser nula). `CheckConstraint`
    garantiza bolsa_total >= 0.
    """

    gestion = models.ForeignKey(
        'gestion.GestionFiscal', on_delete=models.CASCADE,
        related_name='distribuciones_territoriales',
        help_text='Gestión fiscal de la distribución territorial.',
    )
    version = models.ForeignKey(
        DistributionVersion, null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='distribuciones_territoriales',
        help_text='Versión de distribución activa al momento de aplicar.',
    )
    fuente = models.ForeignKey(
        'catalogos.FuenteFinanciamiento', null=True, blank=True,
        on_delete=models.PROTECT, related_name='distribuciones_territoriales',
        help_text='Fuente de la bolsa (sobre la que se reserva).',
    )
    organismo = models.ForeignKey(
        'catalogos.OrganismoFinanciador', null=True, blank=True,
        on_delete=models.PROTECT, related_name='distribuciones_territoriales',
    )
    metodo = models.CharField(
        max_length=20, choices=MetodoDistribucion.CHOICES,
        default=MetodoDistribucion.MANUAL,
    )
    bolsa_total = models.DecimalField(
        max_digits=18, decimal_places=2, verbose_name='Bolsa total (Bs)'
    )
    estado = models.CharField(
        max_length=20, choices=EstadoDistribucionTerritorial.CHOICES,
        default=EstadoDistribucionTerritorial.BORRADOR,
    )
    observaciones = models.TextField(blank=True, default='')

    class Meta:
        verbose_name = 'Distribución territorial'
        verbose_name_plural = 'Distribuciones territoriales'
        ordering = ['-created_at']
        constraints = [
            models.CheckConstraint(
                condition=models.Q(bolsa_total__gte=0),
                name='check_territorialdistribution_bolsa_positiva',
            ),
        ]
        indexes = [
            models.Index(fields=['gestion']),
        ]

    def __str__(self):
        return (
            f'Reparto {self.get_metodo_display()} {self.bolsa_total} '
            f'({self.gestion.anio}, {self.get_estado_display()})'
        )


class TerritorialAllocation(TimeStampedModel):
    """Asignación de un distrito dentro de una distribución territorial.

    `poblacion` alimenta el método POBLACION y `porcentaje` el método
    PORCENTAJE (escala 0-100, documentado en `territorial.calcular_reparto`).
    `monto_calculado`/`ajuste`/`monto_final` los calcula el servicio de
    reparto; la invariante es SUM(monto_final) = bolsa_total de la
    distribución, EXACTO. `UniqueConstraint(nulls_distinct=False)` garantiza
    una fila por (distribucion, distrito).
    """

    distribucion = models.ForeignKey(
        TerritorialDistribution, on_delete=models.CASCADE,
        related_name='asignaciones',
    )
    distrito = models.ForeignKey(
        'territorio.Distrito', on_delete=models.PROTECT,
        related_name='asignaciones_territoriales',
    )
    poblacion = models.PositiveIntegerField(
        null=True, blank=True,
        help_text='Población del distrito (método POBLACION).',
    )
    porcentaje = models.DecimalField(
        max_digits=7, decimal_places=4, null=True, blank=True,
        help_text='Porcentaje del distrito (método PORCENTAJE, escala 0-100).',
    )
    monto_calculado = models.DecimalField(
        max_digits=18, decimal_places=2, default=0,
        verbose_name='Monto calculado (Bs)',
    )
    ajuste = models.DecimalField(
        max_digits=18, decimal_places=2, default=0,
        help_text='Ajuste de redondeo aplicado (monto_final - monto_calculado).',
    )
    monto_final = models.DecimalField(
        max_digits=18, decimal_places=2, default=0,
        verbose_name='Monto final (Bs)',
    )

    class Meta:
        verbose_name = 'Asignación territorial'
        verbose_name_plural = 'Asignaciones territoriales'
        ordering = ['distribucion', 'id']
        constraints = [
            models.UniqueConstraint(
                fields=['distribucion', 'distrito'],
                name='uniq_distribucion_territorial_distrito',
                nulls_distinct=False,
            ),
        ]

    def __str__(self):
        return f'{self.distrito}: {self.monto_final}'


# ---------------------------------------------------------------------------
# Fase 9 - Objetos del gasto: programación por apertura (techo/programado/
# disponible; §90-91). Requiere versión de distribución FIJADA y monto <=
# disponible de la apertura (BUDGET_EXCEEDED en caso contrario).
# ---------------------------------------------------------------------------
class ExpenseObjectAllocation(TimeStampedModel):
    """Programación de un objeto del gasto en una apertura (Fase 9).

    Cada fila programa un `catalogos.ObjetoGasto` (código 5 dígitos
    jerárquico, versionado) contra el techo de la apertura (`Allocation`).
    El control de disponibilidad vive en `BudgetControlService`
    (control.py) y `services.programar_objeto_gasto`. Una fila por
    (allocation, objeto_gasto) con monto >= 0 (`CheckConstraint`).
    """

    allocation = models.ForeignKey(
        Allocation, on_delete=models.CASCADE, related_name='objetos_gasto',
        help_text='Apertura programática de la programación.',
    )
    objeto_gasto = models.ForeignKey(
        'catalogos.ObjetoGasto', on_delete=models.PROTECT,
        related_name='programaciones',
        help_text='Objeto del gasto del clasificador (5 dígitos).',
    )
    monto = models.DecimalField(
        max_digits=18, decimal_places=2, verbose_name='Monto (Bs)'
    )

    class Meta:
        verbose_name = 'Objeto del gasto programado'
        verbose_name_plural = 'Objetos del gasto programados'
        ordering = ['allocation', 'id']
        constraints = [
            models.CheckConstraint(
                condition=models.Q(monto__gte=0),
                name='check_expenseobjectallocation_monto_positivo',
            ),
            models.UniqueConstraint(
                fields=['allocation', 'objeto_gasto'],
                name='uniq_allocation_objeto_gasto',
            ),
        ]
        indexes = [
            models.Index(fields=['allocation', 'objeto_gasto']),
        ]

    def __str__(self):
        return f'{self.objeto_gasto.codigo}: {self.monto}'


class ImportError(TimeStampedModel):
    """Hallazgo de la validación de una importación, con severidad y acción.

    Los CRITICAL sin resolver bloquean la aplicación de la importación.
    """

    importacion = models.ForeignKey(
        BudgetImport, on_delete=models.CASCADE, related_name='errores',
    )
    detalle = models.ForeignKey(
        ImportDetalle, null=True, blank=True,
        on_delete=models.CASCADE, related_name='errores',
    )
    fila = models.PositiveIntegerField(default=0)
    campo = models.CharField(max_length=50, blank=True, default='')
    valor_original = models.TextField(blank=True, default='')
    valor_normalizado = models.TextField(blank=True, default='')
    severidad = models.CharField(
        max_length=20, choices=SeveridadError.CHOICES,
        default=SeveridadError.INFO,
    )
    mensaje = models.TextField(blank=True, default='')
    accion = models.CharField(
        max_length=20, choices=AccionError.CHOICES,
        default=AccionError.NINGUNA,
    )
    resuelto = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Error de importación'
        verbose_name_plural = 'Errores de importación'
        ordering = ['importacion', 'severidad', 'fila']
        indexes = [
            models.Index(fields=['importacion', 'severidad']),
        ]

    def __str__(self):
        return f'[{self.severidad}] {self.campo} fila {self.fila}: {self.mensaje}'
