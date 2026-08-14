"""Modelos del dominio de preinversión SIS-PRO (SISPRE / RM 115).

Expediente estructurado de preinversión municipal: condiciones previas,
ITCP, TDR y presupuesto referencial del EDTP, EDTP con secciones dinámicas
por tipología, estudios técnicos, costos, financiamiento, evaluación,
documentos versionados, revisiones/observaciones/aprobaciones y patrón
Outbox para integraciones con SISPOA/SISPRO.
"""
import hashlib
import uuid
from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models

from apps.core.models import UUIDModel, TimeStampedModel


class EstadosDocumentoPreinversion:
    BORRADOR = 'borrador'
    EN_REVISION = 'en_revision'
    OBSERVADO = 'observado'
    APROBADO = 'aprobado'
    RECHAZADO = 'rechazado'

    CHOICES = [
        (BORRADOR, 'Borrador'),
        (EN_REVISION, 'En revisión'),
        (OBSERVADO, 'Observado'),
        (APROBADO, 'Aprobado'),
        (RECHAZADO, 'Rechazado'),
    ]


class EstadoCondicion:
    PENDIENTE = 'pendiente'
    EN_ELABORACION = 'en_elaboracion'
    OBSERVADA = 'observada'
    SUBSANADA = 'subsanada'
    CUMPLE = 'cumple'
    NO_APLICA = 'no_aplica'
    APROBADA = 'aprobada'

    CHOICES = [
        (PENDIENTE, 'Pendiente'),
        (EN_ELABORACION, 'En elaboración'),
        (OBSERVADA, 'Observada'),
        (SUBSANADA, 'Subsanada'),
        (CUMPLE, 'Cumple'),
        (NO_APLICA, 'No aplica'),
        (APROBADA, 'Aprobada'),
    ]

    RESUELTAS = [CUMPLE, APROBADA, NO_APLICA]


class ResultadoPreliminarITCP:
    VIABLE_EDTP = 'viable_edtp'
    VIABLE_CONDICIONES = 'viable_condiciones'
    NO_VIABLE = 'no_viable'
    INFORMACION_INSUFICIENTE = 'informacion_insuficiente'

    CHOICES = [
        (VIABLE_EDTP, 'Viable para elaborar EDTP'),
        (VIABLE_CONDICIONES, 'Viable con condiciones'),
        (NO_VIABLE, 'No viable'),
        (INFORMACION_INSUFICIENTE, 'Información insuficiente'),
    ]


class ResultadoViabilidadEDTP:
    VIABLE = 'viable'
    VIABLE_CONDICIONES = 'viable_condiciones'
    NO_VIABLE = 'no_viable'
    SUSPENDIDO = 'suspendido'

    CHOICES = [
        (VIABLE, 'Viable'),
        (VIABLE_CONDICIONES, 'Viable con condiciones'),
        (NO_VIABLE, 'No viable'),
        (SUSPENDIDO, 'Suspendido'),
    ]


class SeveridadObservacion:
    BAJA = 'baja'
    MEDIA = 'media'
    ALTA = 'alta'
    CRITICA = 'critica'

    CHOICES = [
        (BAJA, 'Baja'),
        (MEDIA, 'Media'),
        (ALTA, 'Alta'),
        (CRITICA, 'Crítica'),
    ]


# ---------------------------------------------------------------------------
# Proyecto: componentes, beneficiarios, alternativas
# ---------------------------------------------------------------------------
class ComponenteProyecto(UUIDModel, TimeStampedModel):
    """Componente del proyecto de preinversión."""

    proyecto = models.ForeignKey(
        'inversion.Proyecto', on_delete=models.CASCADE, related_name='componentes',
    )
    codigo = models.CharField(max_length=50)
    nombre = models.CharField(max_length=255)
    descripcion = models.TextField(blank=True, default='')
    meta_fisica = models.DecimalField(
        max_digits=18, decimal_places=4, null=True, blank=True,
    )
    unidad = models.CharField(max_length=50, blank=True, default='')
    presupuesto = models.DecimalField(
        max_digits=18, decimal_places=2, default=0,
    )
    orden = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = 'Componente de proyecto'
        verbose_name_plural = 'Componentes de proyecto'
        ordering = ['orden', 'codigo']
        constraints = [
            models.UniqueConstraint(
                fields=['proyecto', 'codigo'], name='uniq_componente_codigo',
            ),
        ]

    def __str__(self):
        return f'{self.proyecto} — {self.codigo} {self.nombre}'


class GrupoBeneficiario(UUIDModel, TimeStampedModel):
    """Grupo de beneficiarios con metodología de cuantificación y fuente."""

    TIPO_CHOICES = [
        ('directo', 'Directo'),
        ('indirecto', 'Indirecto'),
    ]

    proyecto = models.ForeignKey(
        'inversion.Proyecto', on_delete=models.CASCADE,
        related_name='grupos_beneficiarios',
    )
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='directo')
    descripcion = models.CharField(max_length=255)
    cantidad = models.PositiveIntegerField(default=0)
    unidad = models.CharField(max_length=50, default='personas')
    metodologia = models.TextField(blank=True, default='')
    fuente = models.CharField(max_length=255, blank=True, default='')
    fecha_fuente = models.DateField(null=True, blank=True)
    referencia_fuente = models.CharField(max_length=500, blank=True, default='')

    class Meta:
        verbose_name = 'Grupo de beneficiarios'
        verbose_name_plural = 'Grupos de beneficiarios'

    def __str__(self):
        return f'{self.proyecto} — {self.descripcion}'


class AlternativaProyecto(UUIDModel, TimeStampedModel):
    """Alternativa técnica/económica evaluada para el proyecto."""

    proyecto = models.ForeignKey(
        'inversion.Proyecto', on_delete=models.CASCADE, related_name='alternativas',
    )
    codigo = models.CharField(max_length=20)
    nombre = models.CharField(max_length=255)
    descripcion = models.TextField(default='')
    costo_estimado = models.DecimalField(
        max_digits=18, decimal_places=2, null=True, blank=True,
    )
    seleccionada = models.BooleanField(default=False)
    justificacion_seleccion = models.TextField(blank=True, default='')

    class Meta:
        verbose_name = 'Alternativa de proyecto'
        verbose_name_plural = 'Alternativas de proyecto'

    def __str__(self):
        return f'{self.proyecto} — {self.codigo} {self.nombre}'


class SolicitudReformulacion(UUIDModel, TimeStampedModel):
    """Solicitud de reformulación originada por SISPOA u otro sistema."""

    proyecto = models.ForeignKey(
        'inversion.Proyecto', on_delete=models.CASCADE,
        related_name='solicitudes_reformulacion',
    )
    sistema_origen = models.CharField(max_length=50, default='SISPOA')
    motivo = models.TextField()
    presupuesto_propuesto = models.DecimalField(
        max_digits=18, decimal_places=2, null=True, blank=True,
    )
    estado = models.CharField(max_length=30, default='abierta')
    resuelta_en = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Solicitud de reformulación'
        verbose_name_plural = 'Solicitudes de reformulación'

    def __str__(self):
        return f'{self.proyecto} — reformulación {self.sistema_origen}'


# ---------------------------------------------------------------------------
# ITCP — Informe Técnico de Condiciones Previas
# ---------------------------------------------------------------------------
class ITCP(UUIDModel, TimeStampedModel):
    """Informe Técnico de Condiciones Previas (Parte A) por proyecto."""

    proyecto = models.OneToOneField(
        'inversion.Proyecto', on_delete=models.CASCADE, related_name='itcp',
    )
    version = models.PositiveIntegerField(default=1)
    estado = models.CharField(
        max_length=20, choices=EstadosDocumentoPreinversion.CHOICES,
        default=EstadosDocumentoPreinversion.BORRADOR,
    )
    justificacion_iniciativa = models.TextField(blank=True, default='')
    idea_proyecto = models.TextField(blank=True, default='')
    resultado_preliminar = models.CharField(
        max_length=40, choices=ResultadoPreliminarITCP.CHOICES, blank=True, default='',
    )
    conclusiones = models.TextField(blank=True, default='')
    recomendaciones = models.TextField(blank=True, default='')
    aprobado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        related_name='itcps_aprobados', on_delete=models.SET_NULL,
    )
    aprobado_en = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'ITCP'
        verbose_name_plural = 'ITCPs'

    def __str__(self):
        return f'ITCP {self.proyecto} v{self.version}'


class CondicionITCP(UUIDModel, TimeStampedModel):
    """Condición previa verificable del ITCP (RM 115 §ITCP)."""

    CATEGORIA_CHOICES = [
        ('derecho_propietario', 'Derecho propietario'),
        ('uso_suelo', 'Compatibilidad de uso de suelo'),
        ('terceros', 'Derecho de vía / afectaciones'),
        ('riesgo', 'Riesgos no mitigables'),
        ('competencia_institucional', 'Competencia institucional'),
    ]

    proyecto = models.ForeignKey(
        'inversion.Proyecto', on_delete=models.CASCADE,
        related_name='condiciones_itcp',
    )
    itcp = models.ForeignKey(
        ITCP, on_delete=models.CASCADE, related_name='condiciones',
    )
    categoria = models.CharField(max_length=40, choices=CATEGORIA_CHOICES)
    titulo = models.CharField(max_length=255)
    estado = models.CharField(
        max_length=20, choices=EstadoCondicion.CHOICES,
        default=EstadoCondicion.PENDIENTE,
    )
    hallazgo = models.TextField(blank=True, default='')
    plan_accion = models.TextField(blank=True, default='')
    justificacion_no_aplica = models.TextField(blank=True, default='')
    unidad_responsable = models.ForeignKey(
        'organizacion.UnidadOrganizacional', null=True, blank=True,
        on_delete=models.PROTECT,
    )
    fecha_limite = models.DateField(null=True, blank=True)
    critica = models.BooleanField(default=False)
    orden = models.PositiveIntegerField(default=0)
    fuente = models.CharField(max_length=255, blank=True, default='')
    fecha_fuente = models.DateField(null=True, blank=True)
    referencia_fuente = models.CharField(max_length=500, blank=True, default='')
    archivo = models.FileField(
        upload_to='preinversion/condiciones/%Y/%m/', null=True, blank=True,
    )
    nombre_archivo = models.CharField(max_length=255, blank=True, default='')

    class Meta:
        verbose_name = 'Condición ITCP'
        verbose_name_plural = 'Condiciones ITCP'
        ordering = ['itcp', 'orden']

    def __str__(self):
        return f'{self.itcp} — {self.categoria}: {self.titulo}'


# ---------------------------------------------------------------------------
# TDR — Términos de Referencia y presupuesto referencial del EDTP
# ---------------------------------------------------------------------------
class TDR(UUIDModel, TimeStampedModel):
    """Términos de Referencia del EDTP (Parte B del ITCP)."""

    proyecto = models.OneToOneField(
        'inversion.Proyecto', on_delete=models.CASCADE, related_name='tdr',
    )
    version = models.PositiveIntegerField(default=1)
    estado = models.CharField(
        max_length=20, choices=EstadosDocumentoPreinversion.CHOICES,
        default=EstadosDocumentoPreinversion.BORRADOR,
    )
    justificacion = models.TextField(blank=True, default='')
    objetivos = models.TextField(blank=True, default='')
    alcance = models.TextField(blank=True, default='')
    actores_responsabilidades = models.TextField(blank=True, default='')
    metodologia = models.TextField(blank=True, default='')
    duracion_dias = models.PositiveIntegerField(null=True, blank=True)
    presupuesto_referencial = models.DecimalField(
        max_digits=18, decimal_places=2, null=True, blank=True,
    )

    class Meta:
        verbose_name = 'TDR del EDTP'
        verbose_name_plural = 'TDRs del EDTP'

    def __str__(self):
        return f'TDR {self.proyecto} v{self.version}'


class ActividadTDR(UUIDModel, TimeStampedModel):
    tdr = models.ForeignKey(TDR, on_delete=models.CASCADE, related_name='actividades')
    codigo = models.CharField(max_length=30)
    descripcion = models.TextField()
    duracion_dias = models.PositiveIntegerField(default=0)
    orden = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = 'Actividad del TDR'
        verbose_name_plural = 'Actividades del TDR'
        ordering = ['tdr', 'orden']

    def __str__(self):
        return f'{self.tdr} — {self.codigo}'


class ProductoTDR(UUIDModel, TimeStampedModel):
    tdr = models.ForeignKey(TDR, on_delete=models.CASCADE, related_name='productos')
    codigo = models.CharField(max_length=30)
    nombre = models.CharField(max_length=255)
    criterios_aceptacion = models.TextField(blank=True, default='')
    dia_entrega = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = 'Producto del TDR'
        verbose_name_plural = 'Productos del TDR'

    def __str__(self):
        return f'{self.tdr} — {self.codigo} {self.nombre}'


class PersonalTDR(UUIDModel, TimeStampedModel):
    tdr = models.ForeignKey(TDR, on_delete=models.CASCADE, related_name='personal')
    rol = models.CharField(max_length=255)
    cantidad = models.PositiveIntegerField(default=1)
    meses = models.DecimalField(max_digits=8, decimal_places=2, default=1)
    dedicacion_porcentaje = models.DecimalField(
        max_digits=5, decimal_places=2, default=100,
    )
    tarifa_mensual = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    requisitos = models.TextField(blank=True, default='')

    class Meta:
        verbose_name = 'Personal del TDR'
        verbose_name_plural = 'Personal del TDR'

    @property
    def subtotal(self):
        return (
            self.cantidad * self.meses
            * (self.dedicacion_porcentaje / Decimal('100'))
            * self.tarifa_mensual
        )

    def __str__(self):
        return f'{self.tdr} — {self.rol}'


class ItemPresupuestoTDR(UUIDModel, TimeStampedModel):
    """Partida del presupuesto referencial del EDTP (memoria de cálculo)."""

    tdr = models.ForeignKey(TDR, on_delete=models.CASCADE, related_name='items_presupuesto')
    categoria = models.CharField(max_length=80)
    descripcion = models.CharField(max_length=255)
    cantidad = models.DecimalField(max_digits=18, decimal_places=4, default=1)
    unidad = models.CharField(max_length=40, default='global')
    costo_unitario = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    memoria_calculo = models.TextField(blank=True, default='')

    class Meta:
        verbose_name = 'Item de presupuesto del TDR'
        verbose_name_plural = 'Items de presupuesto del TDR'

    @property
    def subtotal(self):
        return self.cantidad * self.costo_unitario

    def __str__(self):
        return f'{self.tdr} — {self.descripcion}'


# ---------------------------------------------------------------------------
# EDTP — Estudio de Diseño Técnico de Preinversión
# ---------------------------------------------------------------------------
class EDTP(UUIDModel, TimeStampedModel):
    """Estudio de Diseño Técnico de Preinversión con secciones dinámicas."""

    proyecto = models.OneToOneField(
        'inversion.Proyecto', on_delete=models.CASCADE, related_name='edtp',
    )
    version = models.PositiveIntegerField(default=1)
    estado = models.CharField(
        max_length=20, choices=EstadosDocumentoPreinversion.CHOICES,
        default=EstadosDocumentoPreinversion.BORRADOR,
    )
    resumen_ejecutivo = models.TextField(blank=True, default='')
    metodo_evaluacion = models.CharField(max_length=40, blank=True, default='')
    resultado_viabilidad = models.CharField(
        max_length=40, choices=ResultadoViabilidadEDTP.CHOICES, blank=True, default='',
    )
    conclusiones = models.TextField(blank=True, default='')
    recomendaciones = models.TextField(blank=True, default='')
    aprobado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        related_name='edtps_aprobados', on_delete=models.SET_NULL,
    )
    aprobado_en = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'EDTP'
        verbose_name_plural = 'EDTPs'

    def __str__(self):
        return f'EDTP {self.proyecto} v{self.version}'


class SeccionEDTP(UUIDModel, TimeStampedModel):
    """Sección del EDTP; se activa/desactiva según tipología y complejidad."""

    edtp = models.ForeignKey(EDTP, on_delete=models.CASCADE, related_name='secciones')
    codigo = models.CharField(max_length=30)
    titulo = models.CharField(max_length=255)
    orden = models.PositiveIntegerField(default=0)
    requerida = models.BooleanField(default=True)
    aplicable = models.BooleanField(default=True)
    justificacion_no_aplica = models.TextField(blank=True, default='')
    contenido = models.TextField(blank=True, default='')
    estado = models.CharField(
        max_length=20, choices=EstadosDocumentoPreinversion.CHOICES,
        default=EstadosDocumentoPreinversion.BORRADOR,
    )
    porcentaje_avance = models.PositiveSmallIntegerField(default=0)
    errores_validacion = models.JSONField(default=list, blank=True)
    fuente = models.CharField(max_length=255, blank=True, default='')
    fecha_fuente = models.DateField(null=True, blank=True)
    referencia_fuente = models.CharField(max_length=500, blank=True, default='')

    class Meta:
        verbose_name = 'Sección del EDTP'
        verbose_name_plural = 'Secciones del EDTP'
        ordering = ['edtp', 'orden', 'codigo']
        constraints = [
            models.UniqueConstraint(
                fields=['edtp', 'codigo'], name='uniq_seccion_edtp',
            ),
        ]

    def __str__(self):
        return f'{self.edtp} — {self.codigo} {self.titulo}'


class EstudioTecnico(UUIDModel, TimeStampedModel):
    """Estudio técnico que respalda el EDTP (topografía, suelos, etc.)."""

    edtp = models.ForeignKey(
        EDTP, on_delete=models.CASCADE, related_name='estudios_tecnicos',
    )
    tipo_estudio = models.CharField(max_length=80)
    titulo = models.CharField(max_length=255)
    requerido = models.BooleanField(default=True)
    estado = models.CharField(
        max_length=20, choices=EstadosDocumentoPreinversion.CHOICES,
        default=EstadosDocumentoPreinversion.BORRADOR,
    )
    profesional = models.CharField(max_length=255, blank=True, default='')
    registro_profesional = models.CharField(max_length=100, blank=True, default='')
    fecha_estudio = models.DateField(null=True, blank=True)
    version = models.PositiveIntegerField(default=1)
    conclusiones = models.TextField(blank=True, default='')

    class Meta:
        verbose_name = 'Estudio técnico'
        verbose_name_plural = 'Estudios técnicos'

    def __str__(self):
        return f'{self.edtp} — {self.tipo_estudio}: {self.titulo}'


class ItemCostoEDTP(UUIDModel, TimeStampedModel):
    """Item de costo de inversión del EDTP."""

    edtp = models.ForeignKey(EDTP, on_delete=models.CASCADE, related_name='items_costo')
    componente = models.ForeignKey(
        ComponenteProyecto, null=True, blank=True,
        on_delete=models.PROTECT, related_name='items_costo',
    )
    categoria = models.CharField(max_length=80)
    codigo = models.CharField(max_length=50)
    descripcion = models.CharField(max_length=500)
    unidad = models.CharField(max_length=40)
    cantidad = models.DecimalField(max_digits=18, decimal_places=4)
    precio_unitario = models.DecimalField(max_digits=18, decimal_places=4)
    fuente = models.CharField(max_length=255, blank=True, default='')
    fecha_fuente = models.DateField(null=True, blank=True)
    referencia_fuente = models.CharField(max_length=500, blank=True, default='')

    class Meta:
        verbose_name = 'Item de costo del EDTP'
        verbose_name_plural = 'Items de costo del EDTP'

    @property
    def subtotal(self):
        return self.cantidad * self.precio_unitario

    def __str__(self):
        return f'{self.edtp} — {self.codigo} {self.descripcion}'


class FuenteFinanciamientoEDTP(UUIDModel, TimeStampedModel):
    edtp = models.ForeignKey(
        EDTP, on_delete=models.CASCADE, related_name='fuentes_financiamiento',
    )
    codigo_fuente = models.CharField(max_length=80)
    nombre_fuente = models.CharField(max_length=255)
    monto = models.DecimalField(max_digits=18, decimal_places=2)
    confirmada = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Fuente de financiamiento del EDTP'
        verbose_name_plural = 'Fuentes de financiamiento del EDTP'

    def __str__(self):
        return f'{self.edtp} — {self.codigo_fuente}: {self.monto}'


class ItemCronograma(UUIDModel, TimeStampedModel):
    """Cronograma físico-financiero del EDTP."""

    edtp = models.ForeignKey(
        EDTP, on_delete=models.CASCADE, related_name='cronograma',
    )
    componente = models.ForeignKey(
        ComponenteProyecto, null=True, blank=True, on_delete=models.PROTECT,
    )
    nombre = models.CharField(max_length=255)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    monto_planificado = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    peso_fisico = models.DecimalField(max_digits=7, decimal_places=4, default=0)

    class Meta:
        verbose_name = 'Item de cronograma'
        verbose_name_plural = 'Items de cronograma'

    def __str__(self):
        return f'{self.edtp} — {self.nombre}'


class PlanOperacionMantenimiento(UUIDModel, TimeStampedModel):
    """Plan de operación y mantenimiento del proyecto."""

    edtp = models.OneToOneField(
        EDTP, on_delete=models.CASCADE, related_name='plan_om',
    )
    operador = models.CharField(max_length=255, blank=True, default='')
    actividades = models.TextField(blank=True, default='')
    costo_operacion_anual = models.DecimalField(
        max_digits=18, decimal_places=2, default=0,
    )
    costo_mantenimiento_anual = models.DecimalField(
        max_digits=18, decimal_places=2, default=0,
    )
    mecanismo_financiamiento = models.TextField(blank=True, default='')
    justificacion_costo_cero = models.TextField(blank=True, default='')

    class Meta:
        verbose_name = 'Plan de operación y mantenimiento'
        verbose_name_plural = 'Planes de operación y mantenimiento'

    def __str__(self):
        return f'POM {self.edtp}'


class IndicadorEvaluacionEDTP(UUIDModel, TimeStampedModel):
    """Indicador de evaluación (VAN, TIR, beneficio/costo, etc.)."""

    edtp = models.ForeignKey(
        EDTP, on_delete=models.CASCADE, related_name='indicadores_evaluacion',
    )
    tipo_indicador = models.CharField(max_length=80)
    nombre = models.CharField(max_length=255)
    valor = models.DecimalField(max_digits=24, decimal_places=6)
    unidad = models.CharField(max_length=80, blank=True, default='')
    interpretacion = models.TextField(blank=True, default='')
    fuente = models.CharField(max_length=255, blank=True, default='')
    fecha_fuente = models.DateField(null=True, blank=True)
    referencia_fuente = models.CharField(max_length=500, blank=True, default='')

    class Meta:
        verbose_name = 'Indicador de evaluación'
        verbose_name_plural = 'Indicadores de evaluación'

    def __str__(self):
        return f'{self.edtp} — {self.nombre}: {self.valor}'


# ---------------------------------------------------------------------------
# Documentos y control de versiones
# ---------------------------------------------------------------------------
class DocumentoPreinversion(UUIDModel, TimeStampedModel):
    """Documento del expediente con versionado y hash SHA-256."""

    proyecto = models.ForeignKey(
        'inversion.Proyecto', on_delete=models.CASCADE, related_name='documentos_preinv',
    )
    tipo_documento = models.CharField(max_length=80)
    titulo = models.CharField(max_length=500)
    etapa = models.CharField(max_length=50, blank=True, default='')
    estado = models.CharField(max_length=30, default='borrador')
    version_actual = models.PositiveIntegerField(default=1)
    metadatos = models.JSONField(default=dict, blank=True)

    class Meta:
        verbose_name = 'Documento de preinversión'
        verbose_name_plural = 'Documentos de preinversión'
        ordering = ['proyecto', '-created_at']

    def __str__(self):
        return f'{self.proyecto} — {self.tipo_documento}: {self.titulo}'


class VersionDocumentoPreinversion(UUIDModel, TimeStampedModel):
    documento = models.ForeignKey(
        DocumentoPreinversion, on_delete=models.CASCADE, related_name='versiones',
    )
    version = models.PositiveIntegerField()
    archivo = models.FileField(upload_to='preinversion/documentos/%Y/%m/')
    nombre_archivo = models.CharField(max_length=500)
    mime_type = models.CharField(max_length=120, blank=True, default='')
    sha256 = models.CharField(max_length=64, blank=True, default='')
    firmado = models.BooleanField(default=False)
    notas = models.TextField(blank=True, default='')

    class Meta:
        verbose_name = 'Versión de documento'
        verbose_name_plural = 'Versiones de documento'
        ordering = ['documento', '-version']
        constraints = [
            models.UniqueConstraint(
                fields=['documento', 'version'], name='uniq_version_documento',
            ),
        ]

    def calcular_hash(self):
        digest = hashlib.sha256()
        for chunk in self.archivo.chunks():
            digest.update(chunk)
        self.sha256 = digest.hexdigest()
        return self.sha256

    def __str__(self):
        return f'{self.documento} v{self.version}'


class DocumentoGenerado(UUIDModel, TimeStampedModel):
    """Registro de generación DOCX/PDF del expediente."""

    proyecto = models.ForeignKey(
        'inversion.Proyecto', on_delete=models.CASCADE,
        related_name='documentos_generados',
    )
    tipo_documento = models.CharField(max_length=20)
    estado = models.CharField(max_length=30, default='encolado')
    plantilla = models.CharField(max_length=255, blank=True, default='')
    archivo_docx = models.FileField(
        upload_to='preinversion/generados/%Y/%m/', null=True, blank=True,
    )
    archivo_pdf = models.FileField(
        upload_to='preinversion/generados/%Y/%m/', null=True, blank=True,
    )
    mensaje_error = models.TextField(blank=True, default='')
    contexto = models.JSONField(default=dict, blank=True)

    class Meta:
        verbose_name = 'Documento generado'
        verbose_name_plural = 'Documentos generados'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.proyecto} — {self.tipo_documento} [{self.estado}]'


# ---------------------------------------------------------------------------
# Revisión, observaciones y aprobaciones
# ---------------------------------------------------------------------------
class RevisionPreinversion(UUIDModel, TimeStampedModel):
    proyecto = models.ForeignKey(
        'inversion.Proyecto', on_delete=models.CASCADE, related_name='revisiones',
    )
    etapa = models.CharField(max_length=40)
    tipo_revision = models.CharField(max_length=50)
    unidad_asignada = models.ForeignKey(
        'organizacion.UnidadOrganizacional', null=True, blank=True,
        on_delete=models.PROTECT,
    )
    usuario_asignado = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL,
    )
    estado = models.CharField(max_length=30, default='pendiente')
    fecha_limite = models.DateField(null=True, blank=True)
    completada_en = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Revisión de preinversión'
        verbose_name_plural = 'Revisiones de preinversión'

    def __str__(self):
        return f'{self.proyecto} — {self.etapa}/{self.tipo_revision}'


class ObservacionPreinversion(UUIDModel, TimeStampedModel):
    proyecto = models.ForeignKey(
        'inversion.Proyecto', on_delete=models.CASCADE, related_name='observaciones',
    )
    revision = models.ForeignKey(
        RevisionPreinversion, null=True, blank=True,
        on_delete=models.CASCADE, related_name='observaciones',
    )
    codigo = models.CharField(max_length=40)
    referencia_seccion = models.CharField(max_length=120, blank=True, default='')
    severidad = models.CharField(
        max_length=20, choices=SeveridadObservacion.CHOICES,
        default=SeveridadObservacion.MEDIA,
    )
    descripcion = models.TextField()
    estado = models.CharField(max_length=20, default='abierta')
    respuesta = models.TextField(blank=True, default='')
    resuelta_en = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Observación de preinversión'
        verbose_name_plural = 'Observaciones de preinversión'

    def __str__(self):
        return f'{self.proyecto} — {self.codigo} ({self.severidad})'


class AprobacionPreinversion(UUIDModel, TimeStampedModel):
    proyecto = models.ForeignKey(
        'inversion.Proyecto', on_delete=models.CASCADE, related_name='aprobaciones',
    )
    etapa = models.CharField(max_length=40)
    nivel_aprobacion = models.CharField(max_length=80)
    aprobador = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
    )
    estado = models.CharField(max_length=20, default='pendiente')
    fecha_decision = models.DateTimeField(null=True, blank=True)
    comentarios = models.TextField(blank=True, default='')
    numero_instrumento = models.CharField(max_length=120, blank=True, default='')

    class Meta:
        verbose_name = 'Aprobación de preinversión'
        verbose_name_plural = 'Aprobaciones de preinversión'

    def __str__(self):
        return f'{self.proyecto} — {self.etapa} ({self.estado})'


# ---------------------------------------------------------------------------
# Interoperabilidad
# ---------------------------------------------------------------------------
class ReferenciaExterna(UUIDModel, TimeStampedModel):
    """Códigos externos de SIS PAD-PEI, SISPOA, SISPRO y SISFIN."""

    proyecto = models.ForeignKey(
        'inversion.Proyecto', on_delete=models.CASCADE,
        related_name='referencias_externas',
    )
    sistema = models.CharField(max_length=40)
    id_externo = models.CharField(max_length=255)
    codigo_externo = models.CharField(max_length=255, blank=True, default='')
    ultima_sincronizacion = models.DateTimeField(null=True, blank=True)
    metadatos = models.JSONField(default=dict, blank=True)

    class Meta:
        verbose_name = 'Referencia externa'
        verbose_name_plural = 'Referencias externas'
        constraints = [
            models.UniqueConstraint(
                fields=['sistema', 'id_externo'], name='uniq_referencia_externa',
            ),
        ]

    def __str__(self):
        return f'{self.proyecto} — {self.sistema}:{self.id_externo}'


class EventoOutbox(UUIDModel, TimeStampedModel):
    """Patrón Outbox: eventos de dominio para integraciones confiables."""

    event_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    tipo_agregado = models.CharField(max_length=80)
    id_agregado = models.UUIDField()
    tipo_evento = models.CharField(max_length=120)
    payload = models.JSONField(default=dict)
    estado = models.CharField(max_length=20, default='pendiente')
    intentos = models.PositiveIntegerField(default=0)
    publicado_en = models.DateTimeField(null=True, blank=True)
    ultimo_error = models.TextField(blank=True, default='')

    class Meta:
        verbose_name = 'Evento outbox'
        verbose_name_plural = 'Eventos outbox'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.tipo_evento} [{self.estado}]'


class MensajeEntrante(UUIDModel, TimeStampedModel):
    """Mensaje entrante idempotente de sistemas externos."""

    sistema_origen = models.CharField(max_length=40)
    clave_idempotencia = models.CharField(max_length=255, unique=True)
    tipo_mensaje = models.CharField(max_length=120)
    payload = models.JSONField(default=dict)
    procesado = models.BooleanField(default=False)
    error = models.TextField(blank=True, default='')

    class Meta:
        verbose_name = 'Mensaje entrante'
        verbose_name_plural = 'Mensajes entrantes'

    def __str__(self):
        return f'{self.sistema_origen}: {self.tipo_mensaje}'
