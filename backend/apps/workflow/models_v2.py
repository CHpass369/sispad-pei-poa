"""Workflow configurable V2 (WP-08 / plan maestro §19.1).

Definiciones y transiciones parametrizables por entidad (instrumentos,
modificaciones, proyectos). Las transiciones declaran capacidades requeridas
(ADR-003); las versiones aprobadas del kernel permanecen inmutables.
"""
import uuid

from django.db import models


class EstadosTarea:
    PENDIENTE = 'pendiente'
    EN_CURSO = 'en_curso'
    COMPLETADA = 'completada'
    RECHAZADA = 'rechazada'

    CHOICES = [
        (PENDIENTE, 'Pendiente'),
        (EN_CURSO, 'En curso'),
        (COMPLETADA, 'Completada'),
        (RECHAZADA, 'Rechazada'),
    ]


class WorkflowDefinition(models.Model):
    """Plantilla de flujo configurable para un tipo de entidad."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    codigo = models.CharField(max_length=100, unique=True)
    nombre = models.CharField(max_length=200)
    tipo_entidad = models.CharField(max_length=50)
    descripcion = models.TextField(blank=True, default='')
    activo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Definición de workflow'
        verbose_name_plural = 'Definiciones de workflow'
        ordering = ['codigo']

    def __str__(self):
        return f'[{self.codigo}] {self.nombre}'


class WorkflowStepDefinition(models.Model):
    """Paso del flujo; `estado` es el estado de la entidad al alcanzarlo."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    definicion = models.ForeignKey(
        WorkflowDefinition, related_name='pasos', on_delete=models.CASCADE,
    )
    orden = models.PositiveIntegerField()
    nombre = models.CharField(max_length=200)
    estado = models.CharField(max_length=50)
    es_inicial = models.BooleanField(default=False)
    es_final = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Paso de workflow'
        verbose_name_plural = 'Pasos de workflow'
        ordering = ['definicion', 'orden']
        constraints = [
            models.UniqueConstraint(
                fields=['definicion', 'orden'],
                name='uniq_paso_workflow_orden',
            ),
        ]

    def __str__(self):
        return f'{self.definicion.codigo} / {self.orden}. {self.nombre}'


class WorkflowTransition(models.Model):
    """Transición configurable entre pasos con capacidades requeridas."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    definicion = models.ForeignKey(
        WorkflowDefinition, related_name='transiciones',
        on_delete=models.CASCADE,
    )
    desde_paso = models.ForeignKey(
        WorkflowStepDefinition, null=True, blank=True,
        related_name='transiciones_salientes', on_delete=models.CASCADE,
    )
    hacia_paso = models.ForeignKey(
        WorkflowStepDefinition, related_name='transiciones_entrantes',
        on_delete=models.CASCADE,
    )
    nombre = models.CharField(max_length=200)
    capacidades_requeridas = models.JSONField(default=list, blank=True)
    requiere_aprobacion = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Transición de workflow'
        verbose_name_plural = 'Transiciones de workflow'
        ordering = ['definicion', 'id']

    def __str__(self):
        origen = self.desde_paso.nombre if self.desde_paso else '(inicio)'
        return f'{origen} → {self.hacia_paso.nombre}'


class WorkflowInstance(models.Model):
    """Instancia de flujo para una entidad concreta (tipo + id genérico)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    definicion = models.ForeignKey(
        WorkflowDefinition, related_name='instancias', on_delete=models.PROTECT,
    )
    entidad_tipo = models.CharField(max_length=50)
    entidad_id = models.UUIDField()
    estado_actual = models.CharField(max_length=50)
    paso_actual = models.ForeignKey(
        WorkflowStepDefinition, null=True, blank=True,
        related_name='instancias_en_paso', on_delete=models.SET_NULL,
    )
    iniciado_por = models.ForeignKey(
        'accounts.Usuario', null=True, blank=True,
        related_name='workflows_iniciados', on_delete=models.SET_NULL,
    )
    cerrado = models.BooleanField(default=False)
    iniciado_en = models.DateTimeField(auto_now_add=True)
    cerrado_en = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Instancia de workflow'
        verbose_name_plural = 'Instancias de workflow'
        ordering = ['-iniciado_en']
        constraints = [
            models.UniqueConstraint(
                fields=['definicion', 'entidad_tipo', 'entidad_id'],
                condition=models.Q(cerrado=False),
                name='uniq_instancia_abierta_por_entidad',
            ),
        ]

    def __str__(self):
        return f'{self.definicion.codigo} / {self.entidad_tipo}:{self.entidad_id}'


class WorkflowTask(models.Model):
    """Tarea actual de una instancia en un paso."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    instancia = models.ForeignKey(
        WorkflowInstance, related_name='tareas', on_delete=models.CASCADE,
    )
    paso = models.ForeignKey(
        WorkflowStepDefinition, related_name='tareas', on_delete=models.PROTECT,
    )
    asignado_a = models.ForeignKey(
        'accounts.Usuario', null=True, blank=True,
        related_name='tareas_workflow', on_delete=models.SET_NULL,
    )
    estado = models.CharField(
        max_length=20, choices=EstadosTarea.CHOICES,
        default=EstadosTarea.PENDIENTE,
    )
    creado_en = models.DateTimeField(auto_now_add=True)
    completado_en = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Tarea de workflow'
        verbose_name_plural = 'Tareas de workflow'
        ordering = ['-creado_en']

    def __str__(self):
        return f'{self.instancia} / {self.paso.nombre} ({self.estado})'


class WorkflowObservacion(models.Model):
    """Observación registrada sobre una instancia/tarea (resultado: devuelta)."""

    SEVERIDAD_CHOICES = [
        ('baja', 'Baja'),
        ('moderada', 'Moderada'),
        ('alta', 'Alta'),
        ('bloqueante', 'Bloqueante'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    instancia = models.ForeignKey(
        WorkflowInstance, related_name='observaciones', on_delete=models.CASCADE,
    )
    tarea = models.ForeignKey(
        WorkflowTask, null=True, blank=True, related_name='observaciones',
        on_delete=models.SET_NULL,
    )
    usuario = models.ForeignKey(
        'accounts.Usuario', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='observaciones_workflow',
    )
    texto = models.TextField()
    severidad = models.CharField(
        max_length=20, choices=SEVERIDAD_CHOICES, default='moderada',
    )
    resuelta = models.BooleanField(default=False)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Observación de workflow'
        verbose_name_plural = 'Observaciones de workflow'
        ordering = ['-creado_en']

    def __str__(self):
        return f'{self.instancia} — {self.severidad}'


class WorkflowAprobacion(models.Model):
    """Registro de aprobación/observación de una transición."""

    RESULTADO_CHOICES = [
        ('aprobado', 'Aprobado'),
        ('observado', 'Observado'),
        ('rechazado', 'Rechazado'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    instancia = models.ForeignKey(
        WorkflowInstance, related_name='aprobaciones', on_delete=models.CASCADE,
    )
    tarea = models.ForeignKey(
        WorkflowTask, null=True, blank=True, related_name='aprobaciones',
        on_delete=models.SET_NULL,
    )
    aprobado_por = models.ForeignKey(
        'accounts.Usuario', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='aprobaciones_workflow',
    )
    resultado = models.CharField(max_length=20, choices=RESULTADO_CHOICES)
    comentario = models.TextField(blank=True, default='')
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Aprobación de workflow'
        verbose_name_plural = 'Aprobaciones de workflow'
        ordering = ['-creado_en']

    def __str__(self):
        return f'{self.instancia} — {self.resultado}'


class Delegacion(models.Model):
    """Delegación de una tarea de workflow a otro usuario."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tarea = models.ForeignKey(
        WorkflowTask, related_name='delegaciones', on_delete=models.CASCADE,
    )
    delegado_de = models.ForeignKey(
        'accounts.Usuario', related_name='delegaciones_emitidas',
        on_delete=models.CASCADE,
    )
    delegado_a = models.ForeignKey(
        'accounts.Usuario', related_name='delegaciones_recibidas',
        on_delete=models.CASCADE,
    )
    motivo = models.CharField(max_length=300, blank=True, default='')
    vigente_hasta = models.DateField(null=True, blank=True)
    activo = models.BooleanField(default=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Delegación'
        verbose_name_plural = 'Delegaciones'
        ordering = ['-creado_en']

    def __str__(self):
        return f'{self.delegado_de} → {self.delegado_a}'
