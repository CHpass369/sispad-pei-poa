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
