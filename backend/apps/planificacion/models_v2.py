"""Kernel estratégico V2 de PIP-GAMS (WP-04 / SIS-PE).

Modelos genéricos y parametrizables por metodología (ADR-002, ADR-004).
Las matrices oficiales son proyecciones de estas relaciones, no tablas
maestras independientes (plan maestro §7.3).
"""
import hashlib
import json
import uuid
from datetime import date

from django.core.exceptions import ValidationError
from django.db import models, transaction


# ---------------------------------------------------------------------------
# Constantes de estado
# ---------------------------------------------------------------------------
class EstadosInstrumento:
    BORRADOR = 'borrador'
    EN_FORMULACION = 'en_formulacion'
    EN_REVISION = 'en_revision'
    OBSERVADO = 'observado'
    VALIDADO = 'validado'
    APROBADO = 'aprobado'

    CHOICES = [
        (BORRADOR, 'Borrador'),
        (EN_FORMULACION, 'En formulación'),
        (EN_REVISION, 'En revisión'),
        (OBSERVADO, 'Observado'),
        (VALIDADO, 'Validado'),
        (APROBADO, 'Aprobado'),
    ]

    INMUTABLES = {APROBADO}


class EstadosMetodologia:
    BORRADOR = 'borrador'
    PUBLICADA = 'publicada'
    VIGENTE = 'vigente'
    DEPRECADA = 'deprecada'
    RETIRADA = 'retirada'

    CHOICES = [
        (BORRADOR, 'Borrador'),
        (PUBLICADA, 'Publicada'),
        (VIGENTE, 'Vigente'),
        (DEPRECADA, 'Deprecada'),
        (RETIRADA, 'Retirada'),
    ]


class NivelesInstrumento:
    NACIONAL = 'nacional'
    SECTORIAL = 'sectorial'
    TERRITORIAL = 'territorial'
    INSTITUCIONAL = 'institucional'
    OPERATIVO = 'operativo'

    CHOICES = [
        (NACIONAL, 'Nacional'),
        (SECTORIAL, 'Sectorial'),
        (TERRITORIAL, 'Territorial'),
        (INSTITUCIONAL, 'Institucional'),
        (OPERATIVO, 'Operativo'),
    ]


# ---------------------------------------------------------------------------
# Instrumentos y metodologías
# ---------------------------------------------------------------------------
class TipoInstrumento(models.Model):
    """Clasificación de instrumentos (PAD, PEI, PDESA, PGDESA...)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    codigo = models.CharField(max_length=50, unique=True)
    nombre = models.CharField(max_length=200)
    nivel = models.CharField(max_length=20, choices=NivelesInstrumento.CHOICES)
    horizonte_anios = models.PositiveIntegerField(null=True, blank=True)
    entidad_emisora = models.CharField(max_length=200, blank=True, default='')
    activo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Tipo de instrumento'
        verbose_name_plural = 'Tipos de instrumento'
        ordering = ['codigo']

    def __str__(self):
        return f'[{self.codigo}] {self.nombre}'


class VersionMetodologia(models.Model):
    """Metodología parametrizable para un tipo de instrumento (semver)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    codigo = models.CharField(max_length=50, unique=True)
    nombre = models.CharField(max_length=200)
    tipo_instrumento = models.ForeignKey(
        TipoInstrumento, related_name='metodologias', on_delete=models.PROTECT,
    )
    version = models.CharField(max_length=20, default='1.0.0')
    vigente_desde = models.DateField(null=True, blank=True)
    fuente_oficial = models.CharField(max_length=300, blank=True, default='')
    estado = models.CharField(
        max_length=20, choices=EstadosMetodologia.CHOICES,
        default=EstadosMetodologia.BORRADOR,
    )
    esquema_validacion = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Versión de metodología'
        verbose_name_plural = 'Versiones de metodología'
        ordering = ['tipo_instrumento', 'codigo']

    def __str__(self):
        return f'{self.codigo} v{self.version}'


class InstrumentoPlanificacion(models.Model):
    """Instrumento de planificación versionable (PAD, PEI...)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tipo = models.ForeignKey(
        TipoInstrumento, related_name='instrumentos', on_delete=models.PROTECT,
    )
    codigo = models.CharField(max_length=50, unique=True)
    nombre = models.CharField(max_length=300)
    institucion_responsable = models.CharField(max_length=300, blank=True, default='')
    periodo_inicio = models.PositiveIntegerField()
    periodo_fin = models.PositiveIntegerField()
    ambito = models.CharField(max_length=200, blank=True, default='')
    descripcion = models.TextField(blank=True, default='')
    estado = models.CharField(
        max_length=20, choices=EstadosInstrumento.CHOICES,
        default=EstadosInstrumento.BORRADOR,
    )
    creado_por = models.ForeignKey(
        'accounts.Usuario', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='instrumentos_creados',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Instrumento de planificación'
        verbose_name_plural = 'Instrumentos de planificación'
        ordering = ['codigo']

    def __str__(self):
        return f'[{self.codigo}] {self.nombre}'

    def clean(self):
        if self.periodo_fin < self.periodo_inicio:
            raise ValidationError(
                {'periodo_fin': 'El periodo de fin no puede ser anterior al de inicio.'}
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class VersionInstrumento(models.Model):
    """Versión de un instrumento; inmutable al aprobarse."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    instrumento = models.ForeignKey(
        InstrumentoPlanificacion, related_name='versiones',
        on_delete=models.CASCADE,
    )
    numero = models.PositiveIntegerField(default=1)
    etiqueta = models.CharField(max_length=200, blank=True, default='')
    metodologia = models.ForeignKey(
        VersionMetodologia, related_name='versiones_instrumento',
        on_delete=models.PROTECT,
    )
    estado = models.CharField(
        max_length=20, choices=EstadosInstrumento.CHOICES,
        default=EstadosInstrumento.BORRADOR,
    )
    inmutable = models.BooleanField(default=False)
    vigencia_desde = models.DateField(null=True, blank=True)
    vigencia_hasta = models.DateField(null=True, blank=True)
    fecha_aprobacion = models.DateField(null=True, blank=True)
    aprobado_por = models.ForeignKey(
        'accounts.Usuario', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='versiones_aprobadas',
    )
    norma_aprobacion = models.CharField(max_length=300, blank=True, default='')
    motivo_cambio = models.TextField(blank=True, default='')
    checksum = models.CharField(max_length=64, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Versión de instrumento'
        verbose_name_plural = 'Versiones de instrumento'
        ordering = ['instrumento', 'numero']
        constraints = [
            models.UniqueConstraint(
                fields=['instrumento', 'numero'],
                name='uniq_version_instrumento_numero',
            ),
        ]

    def __str__(self):
        return f'{self.instrumento.codigo} v{self.numero}'

    def calcular_checksum(self):
        """SHA-256 de nodos y vínculos de la versión (datos semánticos)."""
        payload = {
            'nodos': list(
                self.nodos.order_by('codigo')
                .values_list('tipo_nodo__codigo', 'codigo', 'nombre', 'padre__codigo', 'orden')
            ),
            'vinculos': list(
                self.vinculos.order_by('origen__codigo', 'destino__codigo')
                .values_list('origen__codigo', 'destino__codigo', 'tipo__codigo', 'ponderacion')
            ),
        }
        return hashlib.sha256(
            json.dumps(payload, ensure_ascii=False, sort_keys=True).encode('utf-8')
        ).hexdigest()

    def aprobar(self, usuario, norma='', fecha=None):
        """Aprueba la versión: la vuelve inmutable y fija su checksum."""
        self.estado = EstadosInstrumento.APROBADO
        self.inmutable = True
        self.fecha_aprobacion = fecha or date.today()
        self.aprobado_por = usuario
        self.norma_aprobacion = norma
        self.checksum = self.calcular_checksum()
        self.save(update_fields=[
            'estado', 'inmutable', 'fecha_aprobacion', 'aprobado_por',
            'norma_aprobacion', 'checksum', 'updated_at',
        ])
        # Las versiones anteriores dejan de ser la vigente (trazabilidad)
        self.instrumento.estado = EstadosInstrumento.APROBADO
        self.instrumento.save(update_fields=['estado', 'updated_at'])

    def verificar_checksum(self):
        return self.checksum == self.calcular_checksum()

    def save(self, *args, **kwargs):
        if self.pk and not kwargs.get('force_insert'):
            original = VersionInstrumento.objects.get(pk=self.pk)
            if original.inmutable:
                raise ValidationError(
                    'No se puede modificar una versión aprobada (inmutable).'
                )
        super().save(*args, **kwargs)


# ---------------------------------------------------------------------------
# Nodos y vínculos estratégicos
# ---------------------------------------------------------------------------
class TipoNodoEstrategico(models.Model):
    """Tipo de nodo parametrizado por metodología (eje, lineamiento...)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    codigo = models.CharField(max_length=50)
    denominacion = models.CharField(max_length=200)
    metodologia = models.ForeignKey(
        VersionMetodologia, related_name='tipos_nodo', on_delete=models.CASCADE,
    )
    nivel_orden = models.PositiveIntegerField(default=1)
    permite_hijos = models.BooleanField(default=True)
    cardinalidad = models.CharField(
        max_length=20, choices=[('uno', 'Uno'), ('muchos', 'Muchos')],
        default='muchos',
    )
    reglas_codigo = models.CharField(max_length=200, blank=True, default='')
    campos_obligatorios = models.JSONField(default=list, blank=True)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Tipo de nodo estratégico'
        verbose_name_plural = 'Tipos de nodo estratégico'
        ordering = ['metodologia', 'nivel_orden', 'codigo']
        constraints = [
            models.UniqueConstraint(
                fields=['metodologia', 'codigo'],
                name='uniq_tipo_nodo_metodologia_codigo',
            ),
        ]

    def __str__(self):
        return f'[{self.metodologia.codigo}] {self.denominacion}'


class NodoEstrategico(models.Model):
    """Elemento de la jerarquía de una versión de instrumento."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    version = models.ForeignKey(
        VersionInstrumento, related_name='nodos', on_delete=models.CASCADE,
    )
    tipo_nodo = models.ForeignKey(
        TipoNodoEstrategico, related_name='nodos', on_delete=models.PROTECT,
    )
    padre = models.ForeignKey(
        'self', null=True, blank=True, related_name='hijos',
        on_delete=models.CASCADE,
    )
    codigo = models.CharField(max_length=100)
    nombre = models.CharField(max_length=300)
    descripcion = models.TextField(blank=True, default='')
    orden = models.PositiveIntegerField(default=0)
    atributos = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Nodo estratégico'
        verbose_name_plural = 'Nodos estratégicos'
        ordering = ['version', 'orden', 'codigo']
        indexes = [
            models.Index(fields=['version', 'tipo_nodo']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['version', 'codigo'],
                name='uniq_nodo_version_codigo',
            ),
        ]

    def __str__(self):
        return f'{self.version} / {self.codigo} {self.nombre}'

    def clean(self):
        errors = {}
        if self.version_id and self.version.inmutable:
            errors['version'] = 'No se puede modificar una versión aprobada (inmutable).'
        if self.padre_id:
            if self.padre.version_id != self.version_id:
                errors['padre'] = 'El padre debe pertenecer a la misma versión.'
            if self.padre_id == self.id:
                errors['padre'] = 'Un nodo no puede ser su propio padre.'
            if not self.padre.tipo_nodo.permite_hijos:
                errors['padre'] = (
                    f'El tipo de nodo "{self.padre.tipo_nodo.denominacion}" '
                    'no permite hijos.'
                )
            # Sin ciclos: el padre no puede descender de este nodo
            ancestro = self.padre
            while ancestro is not None:
                if self.pk and ancestro.pk == self.pk:
                    errors['padre'] = 'La jerarquía generaría un ciclo.'
                    break
                ancestro = ancestro.padre
        if self.tipo_nodo.metodologia_id != self.version.metodologia_id:
            errors['tipo_nodo'] = (
                'El tipo de nodo debe pertenecer a la metodología de la versión.'
            )
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class TipoVinculoEstrategico(models.Model):
    """Tipo de relación articulada entre tipos de nodo (PAD→PEI...)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    codigo = models.CharField(max_length=50)
    denominacion = models.CharField(max_length=200)
    metodologia = models.ForeignKey(
        VersionMetodologia, related_name='tipos_vinculo', on_delete=models.CASCADE,
    )
    origen_permitido = models.ForeignKey(
        TipoNodoEstrategico, related_name='vinculos_origen',
        on_delete=models.CASCADE,
    )
    destino_permitido = models.ForeignKey(
        TipoNodoEstrategico, related_name='vinculos_destino',
        on_delete=models.CASCADE,
    )
    requiere_ponderacion = models.BooleanField(default=False)
    requiere_justificacion = models.BooleanField(default=False)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Tipo de vínculo estratégico'
        verbose_name_plural = 'Tipos de vínculo estratégico'
        ordering = ['metodologia', 'codigo']
        constraints = [
            models.UniqueConstraint(
                fields=['metodologia', 'codigo'],
                name='uniq_tipo_vinculo_metodologia_codigo',
            ),
        ]

    def __str__(self):
        return f'[{self.metodologia.codigo}] {self.denominacion}'


class VinculoEstrategico(models.Model):
    """Vínculo articulado entre dos nodos (matrices = proyecciones)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    version = models.ForeignKey(
        VersionInstrumento, related_name='vinculos', on_delete=models.CASCADE,
    )
    origen = models.ForeignKey(
        NodoEstrategico, related_name='vinculos_origen', on_delete=models.CASCADE,
    )
    destino = models.ForeignKey(
        NodoEstrategico, related_name='vinculos_destino', on_delete=models.CASCADE,
    )
    tipo = models.ForeignKey(
        TipoVinculoEstrategico, related_name='vinculos', on_delete=models.PROTECT,
    )
    es_principal = models.BooleanField(default=False)
    ponderacion = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True,
    )
    justificacion = models.TextField(blank=True, default='')
    validador = models.ForeignKey(
        'accounts.Usuario', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='vinculos_validados',
    )
    fecha_validacion = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Vínculo estratégico'
        verbose_name_plural = 'Vínculos estratégicos'
        ordering = ['version', 'origen', 'destino']
        indexes = [
            models.Index(fields=['version', 'destino']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['version', 'origen', 'destino', 'tipo'],
                name='uniq_vinculo_version_origen_destino_tipo',
            ),
        ]

    def __str__(self):
        return f'{self.origen.codigo} → {self.destino.codigo}'

    def clean(self):
        errors = {}
        if self.version.inmutable:
            errors['version'] = 'No se puede modificar una versión aprobada (inmutable).'
        if self.origen_id == self.destino_id:
            errors['destino'] = 'No se permite la auto-articulación.'
        # El vínculo pertenece a la versión propietaria (origen); el destino
        # puede pertenecer a otra versión (articulación entre instrumentos,
        # p.ej. PAD → marco superior nacional).
        tipo = self.tipo
        if self.origen.tipo_nodo_id != tipo.origen_permitido_id:
            errors['origen'] = (
                f'Origen debe ser un nodo tipo "{tipo.origen_permitido.denominacion}".'
            )
        if self.destino.tipo_nodo_id != tipo.destino_permitido_id:
            errors['destino'] = (
                f'Destino debe ser un nodo tipo "{tipo.destino_permitido.denominacion}".'
            )
        if tipo.requiere_ponderacion and self.ponderacion is None:
            errors['ponderacion'] = 'Este tipo de vínculo requiere ponderación.'
        if self.ponderacion is not None and not (0 <= self.ponderacion <= 100):
            errors['ponderacion'] = 'La ponderación debe estar entre 0 y 100.'
        if tipo.requiere_justificacion and not self.justificacion.strip():
            errors['justificacion'] = 'Este tipo de vínculo requiere justificación.'
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
