"""Modelos V2 del SIS-PRO (WP-11 / plan maestro §14).

Evolución controlada de `inversion` como semilla del sistema de proyectos:
ciclo completo idea → condiciones previas → preinversión → formulación →
costos → revisión → contratación → ejecución → supervisión → cierre →
evaluación, con trazabilidad ascendente Proyecto → POA → PEI → PAD (plan §14.2).

Desde WP-11b (SISPRE) el modelo incorpora el dominio de preinversión:
tipología RM 115, geometría, presupuestos referenciales y estados del
expediente (ITCP → TDR → EDTP → banco de proyectos viables).
"""
import uuid
from decimal import Decimal

from django.contrib.gis.db import models
from django.core.validators import MaxValueValidator, MinValueValidator


class FasesProyecto:
    IDEA = 'idea'
    CONDICIONES_PREVIAS = 'condiciones_previas'
    PREINVERSION = 'preinversion'
    FORMULACION = 'formulacion'
    COSTOS = 'costos'
    REVISION = 'revision'
    CONTRATACION = 'contratacion'
    EJECUCION = 'ejecucion'
    SUPERVISION = 'supervision'
    CIERRE = 'cierre'
    EVALUACION = 'evaluacion'

    CHOICES = [
        (IDEA, 'Idea / Demanda'),
        (CONDICIONES_PREVIAS, 'Condiciones previas'),
        (PREINVERSION, 'Preinversión'),
        (FORMULACION, 'Formulación técnica'),
        (COSTOS, 'Costos y presupuesto'),
        (REVISION, 'Revisión técnico-financiera-legal'),
        (CONTRATACION, 'Contratación'),
        (EJECUCION, 'Ejecución'),
        (SUPERVISION, 'Supervisión / Fiscalización'),
        (CIERRE, 'Recepción / Cierre'),
        (EVALUACION, 'Evaluación'),
    ]

    ORDEN = [c[0] for c in CHOICES]


class EstadosProyecto:
    ACTIVO = 'activo'
    SUSPENDIDO = 'suspendido'
    CERRADO = 'cerrado'

    CHOICES = [
        (ACTIVO, 'Activo'),
        (SUSPENDIDO, 'Suspendido'),
        (CERRADO, 'Cerrado'),
    ]


class EstadosExpedientePreinversion:
    """Estados del expediente de preinversión (SISPRE, RM 115)."""

    REGISTRADA = 'registrada'
    EN_ADMISIBILIDAD = 'en_admisibilidad'
    ADMITIDA = 'admitida'
    ITCP_ELABORACION = 'itcp_elaboracion'
    ITCP_REVISION = 'itcp_revision'
    ITCP_APROBADO = 'itcp_aprobado'
    EDTP_ELABORACION = 'edtp_elaboracion'
    EDTP_REVISION = 'edtp_revision'
    EDTP_APROBADO = 'edtp_aprobado'
    VIABLE = 'viable'
    HABILITADO_POA = 'habilitado_poa'
    ENVIADO_POA = 'enviado_poa'
    NO_VIABLE = 'no_viable'
    ARCHIVADO = 'archivado'

    CHOICES = [
        (REGISTRADA, 'Iniciativa registrada'),
        (EN_ADMISIBILIDAD, 'En admisibilidad'),
        (ADMITIDA, 'Admitida'),
        (ITCP_ELABORACION, 'ITCP en elaboración'),
        (ITCP_REVISION, 'ITCP en revisión'),
        (ITCP_APROBADO, 'ITCP aprobado'),
        (EDTP_ELABORACION, 'EDTP en elaboración'),
        (EDTP_REVISION, 'EDTP en revisión'),
        (EDTP_APROBADO, 'EDTP aprobado'),
        (VIABLE, 'Viable'),
        (HABILITADO_POA, 'Habilitado para programación'),
        (ENVIADO_POA, 'Enviado a SISPOA'),
        (NO_VIABLE, 'No viable'),
        (ARCHIVADO, 'Archivado'),
    ]


class TipologiaRM115:
    """Tipologías de la Resolución Ministerial N.º 115."""

    TIPO_I = 'I'
    TIPO_II = 'II'
    TIPO_III = 'III'
    TIPO_IV = 'IV'
    TIPO_V = 'V'

    CHOICES = [
        (TIPO_I, 'Desarrollo Empresarial Productivo'),
        (TIPO_II, 'Apoyo al Desarrollo Productivo'),
        (TIPO_III, 'Desarrollo Social'),
        (TIPO_IV, 'Fortalecimiento Institucional'),
        (TIPO_V, 'Investigación y Desarrollo Tecnológico'),
    ]


class Proyecto(models.Model):
    """Proyecto de inversión gestionado por su ciclo (SIS-PRO V2)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    codigo_interno = models.CharField(max_length=50, unique=True)
    codigo_sisin = models.CharField(max_length=100, blank=True, default='')
    nombre = models.CharField(max_length=500)
    descripcion = models.TextField(blank=True, default='')
    gestion = models.PositiveIntegerField()
    fase = models.CharField(
        max_length=30, choices=FasesProyecto.CHOICES, default=FasesProyecto.IDEA,
    )
    estado = models.CharField(
        max_length=20, choices=EstadosProyecto.CHOICES,
        default=EstadosProyecto.ACTIVO,
    )
    prioridad = models.PositiveSmallIntegerField(default=4)
    ue = models.ForeignKey(
        'organizacion.UnidadEjecutora', null=True, blank=True,
        related_name='proyectos_v2', on_delete=models.SET_NULL,
    )
    costo_total = models.DecimalField(
        max_digits=20, decimal_places=2, default=0,
    )
    ejecucion_acumulada = models.DecimalField(
        max_digits=20, decimal_places=2, default=0,
    )
    # -- Dominio de preinversión (SISPRE / RM 115) --------------------------
    estado_preinversion = models.CharField(
        max_length=30, choices=EstadosExpedientePreinversion.CHOICES,
        default=EstadosExpedientePreinversion.REGISTRADA,
    )
    tipologia_rm115 = models.CharField(
        max_length=4, choices=TipologiaRM115.CHOICES, blank=True, default='',
    )
    responsable = models.ForeignKey(
        'accounts.Usuario', null=True, blank=True,
        related_name='proyectos_responsables', on_delete=models.SET_NULL,
    )
    problema = models.TextField(blank=True, default='')
    objetivo_general = models.TextField(blank=True, default='')
    descripcion_localizacion = models.TextField(blank=True, default='')
    distrito = models.CharField(max_length=40, blank=True, default='')
    comunidad = models.CharField(max_length=255, blank=True, default='')
    geom = models.GeometryField(srid=32719, null=True, blank=True)
    presupuesto_estimado = models.DecimalField(
        max_digits=18, decimal_places=2, null=True, blank=True,
        validators=[MinValueValidator(Decimal('0'))],
    )
    presupuesto_aprobado = models.DecimalField(
        max_digits=18, decimal_places=2, null=True, blank=True,
        validators=[MinValueValidator(Decimal('0'))],
    )
    moneda = models.CharField(max_length=3, default='BOB')
    puntaje_madurez = models.DecimalField(
        max_digits=5, decimal_places=2, default=0,
        validators=[MinValueValidator(Decimal('0')), MaxValueValidator(Decimal('100'))],
    )
    habilitado_poa = models.BooleanField(default=False)
    vigencia_viabilidad = models.DateField(null=True, blank=True)
    codigos_externos = models.JSONField(default=dict, blank=True)
    etiquetas = models.JSONField(default=list, blank=True)
    atributos = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Proyecto (SIS-PRO V2)'
        verbose_name_plural = 'Proyectos (SIS-PRO V2)'
        ordering = ['gestion', 'codigo_interno']
        indexes = [
            models.Index(fields=['gestion', 'fase']),
            models.Index(fields=['estado_preinversion', 'gestion']),
        ]

    def __str__(self):
        return f'[{self.codigo_interno}] {self.nombre}'

    def avanzar_fase(self):
        """Avanza a la siguiente fase del ciclo (sin saltos)."""
        indice = FasesProyecto.ORDEN.index(self.fase)
        if indice >= len(FasesProyecto.ORDEN) - 1:
            return False, 'El proyecto ya está en la fase final.'
        self.fase = FasesProyecto.ORDEN[indice + 1]
        self.save(update_fields=['fase', 'updated_at'])
        return True, self.fase


class CondicionPrevia(models.Model):
    """Condición previa del proyecto (saneamiento, licencias, financiamiento)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    proyecto = models.ForeignKey(
        Proyecto, related_name='condiciones_previas', on_delete=models.CASCADE,
    )
    descripcion = models.TextField()
    cumplida = models.BooleanField(default=False)
    fecha_cumplimiento = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Condición previa'
        verbose_name_plural = 'Condiciones previas'
        ordering = ['proyecto', 'created_at']

    def __str__(self):
        return f'{self.proyecto.codigo_interno} — {self.descripcion[:60]}'


class DocumentoTecnico(models.Model):
    """Documento técnico del ciclo (ITCP/EDTP/expediente/actas)."""

    TIPO_CHOICES = [
        ('idea', 'Ficha de idea'),
        ('itcp', 'ITCP'),
        ('edtp', 'EDTP'),
        ('expediente', 'Expediente de formulación'),
        ('contrato', 'Contrato'),
        ('acta', 'Acta de recepción'),
        ('evaluacion', 'Informe de evaluación'),
        ('otro', 'Otro'),
    ]

    ESTADO_CHOICES = [
        ('borrador', 'Borrador'),
        ('aprobado', 'Aprobado'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    proyecto = models.ForeignKey(
        Proyecto, related_name='documentos_tecnicos', on_delete=models.CASCADE,
    )
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='otro')
    nombre = models.CharField(max_length=300)
    descripcion = models.TextField(blank=True, default='')
    fecha = models.DateField(null=True, blank=True)
    estado = models.CharField(
        max_length=20, choices=ESTADO_CHOICES, default='borrador',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Documento técnico'
        verbose_name_plural = 'Documentos técnicos'
        ordering = ['proyecto', '-created_at']

    def __str__(self):
        return f'{self.proyecto.codigo_interno} — {self.nombre}'


class CostoProyecto(models.Model):
    """Costo por concepto y año del proyecto."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    proyecto = models.ForeignKey(
        Proyecto, related_name='costos', on_delete=models.CASCADE,
    )
    concepto = models.CharField(max_length=300)
    monto = models.DecimalField(max_digits=20, decimal_places=2)
    anio = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Costo de proyecto'
        verbose_name_plural = 'Costos de proyecto'
        ordering = ['proyecto', 'anio', 'concepto']

    def __str__(self):
        return f'{self.proyecto.codigo_interno} — {self.concepto}: {self.monto}'


class VinculoProyectoActividad(models.Model):
    """Vínculo del proyecto con una actividad del SIS-POA (cadena ascendente)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    proyecto = models.ForeignKey(
        Proyecto, related_name='vinculos_actividad', on_delete=models.CASCADE,
    )
    actividad = models.ForeignKey(
        'poau.Actividad', related_name='proyectos_vinculados',
        on_delete=models.PROTECT,
    )
    es_principal = models.BooleanField(default=True)
    justificacion = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Vínculo proyecto-actividad'
        verbose_name_plural = 'Vínculos proyecto-actividad'
        constraints = [
            models.UniqueConstraint(
                fields=['proyecto', 'actividad'],
                name='uniq_vinculo_proyecto_actividad',
            ),
        ]

    def __str__(self):
        return f'{self.proyecto} → {self.actividad}'


class ProyectoTerritorio(models.Model):
    """Localización territorial del proyecto (PostGIS)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    proyecto = models.ForeignKey(
        Proyecto, related_name='territorios', on_delete=models.CASCADE,
    )
    localizacion = models.ForeignKey(
        'territorio.LocalizacionTerritorial', related_name='proyectos',
        on_delete=models.PROTECT,
    )
    es_principal = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Territorio de proyecto'
        verbose_name_plural = 'Territorios de proyecto'
        constraints = [
            models.UniqueConstraint(
                fields=['proyecto', 'localizacion'],
                name='uniq_proyecto_localizacion',
            ),
        ]

    def __str__(self):
        return f'{self.proyecto} → {self.localizacion}'
