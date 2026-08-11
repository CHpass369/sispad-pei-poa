"""Jerarquía operativa canónica V2 del SIS-POA (WP-10 / plan maestro §13).

Cadena: POA institucional → Acción de corto plazo → Operación → Actividad →
Tarea, con programación físico-financiera. El POA requiere una versión de PEI
aprobada para avanzar a revisión/aprobación (conexión estratégica obligatoria).
"""
import uuid

from django.core.exceptions import ValidationError
from django.db import models


class EstadosPoA:
    BORRADOR = 'borrador'
    EN_FORMULACION = 'en_formulacion'
    EN_REVISION = 'en_revision'
    OBSERVADO = 'observado'
    APROBADO = 'aprobado'

    CHOICES = [
        (BORRADOR, 'Borrador'),
        (EN_FORMULACION, 'En formulación'),
        (EN_REVISION, 'En revisión'),
        (OBSERVADO, 'Observado'),
        (APROBADO, 'Aprobado'),
    ]

    REQUIERE_PEI = {EN_REVISION, APROBADO}


class PoAInstitucional(models.Model):
    """POA institucional consolidado (SIS-POA)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    gestion = models.PositiveIntegerField()
    codigo = models.CharField(max_length=50, unique=True)
    nombre = models.CharField(max_length=300)
    version_pei = models.ForeignKey(
        'planificacion.VersionInstrumento', null=True, blank=True,
        related_name='poas', on_delete=models.SET_NULL,
        help_text='Versión PEI aprobada a la que se articula (obligatoria).',
    )
    estado = models.CharField(
        max_length=20, choices=EstadosPoA.CHOICES, default=EstadosPoA.BORRADOR,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'poau_poainstitucional'
        verbose_name = 'POA institucional'
        verbose_name_plural = 'POAs institucionales'
        ordering = ['gestion', 'codigo']
        indexes = [
            models.Index(fields=['gestion', 'estado']),
        ]

    def __str__(self):
        return f'[{self.codigo}] {self.nombre}'

    def clean(self):
        if self.estado in EstadosPoA.REQUIERE_PEI and not self.version_pei_id:
            raise ValidationError({
                'version_pei': (
                    'El POA no puede pasar a revisión/aprobación sin una '
                    'versión de PEI vinculada (conexión estratégica obligatoria).'
                ),
            })

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class AccionCortoPlazo(models.Model):
    """Descomposición anual del PEI que vincula estrategia con operación."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    poa = models.ForeignKey(
        PoAInstitucional, related_name='acciones', on_delete=models.CASCADE,
    )
    codigo = models.CharField(max_length=50)
    nombre = models.CharField(max_length=500)
    descripcion = models.TextField(blank=True, default='')
    nodo_pei = models.ForeignKey(
        'planificacion.NodoEstrategico', null=True, blank=True,
        related_name='acciones_poa', on_delete=models.SET_NULL,
    )
    unidad = models.ForeignKey(
        'organizacion.UnidadOrganizacional', null=True, blank=True,
        related_name='acciones_poa_v2', on_delete=models.SET_NULL,
    )
    atributos = models.JSONField(default=dict, blank=True)
    estado = models.CharField(
        max_length=20, choices=EstadosPoA.CHOICES, default=EstadosPoA.BORRADOR,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'poau_accioncortoplazo'
        verbose_name = 'Acción de corto plazo'
        verbose_name_plural = 'Acciones de corto plazo'
        ordering = ['poa', 'codigo']
        constraints = [
            models.UniqueConstraint(
                fields=['poa', 'codigo'], name='uniq_accion_poa_codigo',
            ),
        ]

    def __str__(self):
        return f'[{self.codigo}] {self.nombre}'


class Operacion(models.Model):
    """Operación dentro de una acción de corto plazo."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    accion = models.ForeignKey(
        AccionCortoPlazo, related_name='operaciones', on_delete=models.CASCADE,
    )
    codigo = models.CharField(max_length=50)
    nombre = models.CharField(max_length=500)
    unidad = models.ForeignKey(
        'organizacion.UnidadOrganizacional', null=True, blank=True,
        related_name='operaciones_poa', on_delete=models.SET_NULL,
    )
    atributos = models.JSONField(default=dict, blank=True)
    estado = models.CharField(
        max_length=20, choices=EstadosPoA.CHOICES, default=EstadosPoA.BORRADOR,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'poau_operacion'
        verbose_name = 'Operación'
        verbose_name_plural = 'Operaciones'
        ordering = ['accion', 'codigo']
        constraints = [
            models.UniqueConstraint(
                fields=['accion', 'codigo'], name='uniq_operacion_codigo',
            ),
        ]

    def __str__(self):
        return f'[{self.codigo}] {self.nombre}'


class Actividad(models.Model):
    """Actividad dentro de una operación."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    operacion = models.ForeignKey(
        Operacion, related_name='actividades', on_delete=models.CASCADE,
    )
    codigo = models.CharField(max_length=50)
    nombre = models.CharField(max_length=500)
    atributos = models.JSONField(default=dict, blank=True)
    estado = models.CharField(
        max_length=20, choices=EstadosPoA.CHOICES, default=EstadosPoA.BORRADOR,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'poau_actividad'
        verbose_name = 'Actividad'
        verbose_name_plural = 'Actividades'
        ordering = ['operacion', 'codigo']
        constraints = [
            models.UniqueConstraint(
                fields=['operacion', 'codigo'], name='uniq_actividad_codigo',
            ),
        ]

    def __str__(self):
        return f'[{self.codigo}] {self.nombre}'


class Tarea(models.Model):
    """Tarea dentro de una actividad."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    actividad = models.ForeignKey(
        Actividad, related_name='tareas', on_delete=models.CASCADE,
    )
    codigo = models.CharField(max_length=50)
    nombre = models.CharField(max_length=500)
    atributos = models.JSONField(default=dict, blank=True)
    estado = models.CharField(
        max_length=20, choices=EstadosPoA.CHOICES, default=EstadosPoA.BORRADOR,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'poau_tarea'
        verbose_name = 'Tarea'
        verbose_name_plural = 'Tareas'
        ordering = ['actividad', 'codigo']
        constraints = [
            models.UniqueConstraint(
                fields=['actividad', 'codigo'], name='uniq_tarea_codigo',
            ),
        ]

    def __str__(self):
        return f'[{self.codigo}] {self.nombre}'


class ProgramacionActividad(models.Model):
    """Programación físico-financiera anual por actividad."""

    TIPO_FISICA = 'fisica'
    TIPO_FINANCIERA = 'financiera'

    TIPO_CHOICES = [
        (TIPO_FISICA, 'Física'),
        (TIPO_FINANCIERA, 'Financiera'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    actividad = models.ForeignKey(
        Actividad, related_name='programaciones', on_delete=models.CASCADE,
    )
    anio = models.PositiveIntegerField()
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    programado = models.DecimalField(
        max_digits=20, decimal_places=4, default=0,
    )
    ejecutado = models.DecimalField(
        max_digits=20, decimal_places=4, default=0,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'poau_programacionactividad'
        verbose_name = 'Programación de actividad'
        verbose_name_plural = 'Programaciones de actividades'
        ordering = ['actividad', 'anio', 'tipo']
        constraints = [
            models.UniqueConstraint(
                fields=['actividad', 'anio', 'tipo'],
                name='uniq_programacion_actividad',
            ),
        ]

    def __str__(self):
        return f'{self.actividad} {self.anio} ({self.tipo})'

    def clean(self):
        if self.programado < 0 or self.ejecutado < 0:
            raise ValidationError('Programado y ejecutado no pueden ser negativos.')

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
