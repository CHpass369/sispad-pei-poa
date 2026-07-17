import uuid
from django.db import models
from django.conf import settings
from apps.core.models import TimeStampedModel


class ReporteSeguimiento(TimeStampedModel):
    """Reporte consolidado de seguimiento físico-financiero por periodo"""

    ESTADO_CHOICES = [
        ('borrador', 'Borrador'),
        ('enviado', 'Enviado'),
        ('validado', 'Validado'),
        ('aprobado', 'Aprobado'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    gestion = models.PositiveIntegerField(verbose_name='Gestion')
    periodo = models.CharField(
        max_length=20,
        help_text='Formato: 2026-Q1, 2026-S1, 2026',
        verbose_name='Periodo',
    )
    unidad_organizacional = models.ForeignKey(
        'organizacion.UnidadOrganizacional', on_delete=models.PROTECT,
        related_name='reportes_seguimiento',
        verbose_name='Unidad Organizacional',
    )
    estado = models.CharField(
        max_length=20, choices=ESTADO_CHOICES, default='borrador',
        verbose_name='Estado',
    )
    submitted_at = models.DateTimeField(
        null=True, blank=True,
        verbose_name='Fecha de envio',
    )
    approved_at = models.DateTimeField(
        null=True, blank=True,
        verbose_name='Fecha de aprobacion',
    )
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='+',
        verbose_name='Enviado por',
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='+',
        verbose_name='Aprobado por',
    )

    class Meta:
        verbose_name = 'Reporte de seguimiento'
        verbose_name_plural = 'Reportes de seguimiento'
        ordering = ['-gestion', '-periodo']
        unique_together = [('gestion', 'periodo', 'unidad_organizacional')]
        indexes = [
            models.Index(fields=['gestion', 'periodo']),
            models.Index(fields=['estado']),
        ]

    def __str__(self):
        return f'Seguimiento {self.gestion} - {self.periodo} ({self.unidad_organizacional})'


class EntradaSeguimiento(TimeStampedModel):
    """Detalle de seguimiento por actividad del POAU"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reporte = models.ForeignKey(
        ReporteSeguimiento, on_delete=models.CASCADE,
        related_name='entradas',
        verbose_name='Reporte',
    )
    actividad = models.ForeignKey(
        'poau.POAUActividad', on_delete=models.PROTECT,
        related_name='entradas_seguimiento',
        verbose_name='Actividad',
    )

    programado_fisico = models.DecimalField(
        max_digits=20, decimal_places=4, default=0,
        verbose_name='Programado fisico',
    )
    ejecutado_fisico = models.DecimalField(
        max_digits=20, decimal_places=4, default=0,
        verbose_name='Ejecutado fisico',
    )
    porcentaje_avance_fisico = models.DecimalField(
        max_digits=7, decimal_places=2, default=0,
        verbose_name='% Avance fisico',
    )

    presupuesto_inicial = models.DecimalField(
        max_digits=20, decimal_places=2, default=0,
        verbose_name='Presupuesto inicial',
    )
    presupuesto_actual = models.DecimalField(
        max_digits=20, decimal_places=2, default=0,
        verbose_name='Presupuesto actual',
    )
    programado_financiero = models.DecimalField(
        max_digits=20, decimal_places=2, default=0,
        verbose_name='Programado financiero',
    )
    ejecutado_financiero = models.DecimalField(
        max_digits=20, decimal_places=2, default=0,
        verbose_name='Ejecutado financiero',
    )
    porcentaje_avance_financiero = models.DecimalField(
        max_digits=7, decimal_places=2, default=0,
        verbose_name='% Avance financiero',
    )

    desviacion = models.DecimalField(
        max_digits=7, decimal_places=2, default=0,
        verbose_name='Desviacion (%)',
    )
    causa_desviacion = models.TextField(
        blank=True, default='',
        verbose_name='Causa de desviacion',
    )
    accion_correctiva = models.TextField(
        null=True, blank=True,
        verbose_name='Accion correctiva',
    )
    proyeccion_cierre = models.TextField(
        blank=True, default='',
        verbose_name='Proyeccion a fin de gestion',
    )
    evidencia = models.TextField(
        blank=True, default='',
        verbose_name='Evidencia',
    )

    class Meta:
        verbose_name = 'Entrada de seguimiento'
        verbose_name_plural = 'Entradas de seguimiento'
        ordering = ['actividad__codigo']
        unique_together = [('reporte', 'actividad')]
        indexes = [
            models.Index(fields=['reporte', 'actividad']),
        ]

    def __str__(self):
        return f'{self.actividad} - {self.reporte}'


class Alerta(TimeStampedModel):
    """Alerta generada por incumplimiento de umbrales"""

    TIPO_CHOICES = [
        ('ejecucion_fisica_baja', 'Ejecucion fisica baja'),
        ('ejecucion_financiera_baja', 'Ejecucion financiera baja'),
        ('avance_sin_financiera', 'Avance sin financiamiento'),
        ('financiera_sin_avance', 'Financiamiento sin avance'),
        ('sobreejecucion', 'Sobreejecucion'),
        ('meta_vencida', 'Meta vencida'),
        ('sin_evidencia', 'Sin evidencia'),
        ('incumplimiento_correctivo', 'Incumplimiento de accion correctiva'),
        ('presupuesto_sin_actividad', 'Presupuesto sin actividad'),
        ('actividad_sin_presupuesto', 'Actividad sin presupuesto'),
    ]

    SEVERIDAD_CHOICES = [
        ('leve', 'Leve'),
        ('moderada', 'Moderada'),
        ('grave', 'Grave'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    entrada = models.ForeignKey(
        EntradaSeguimiento, on_delete=models.CASCADE,
        related_name='alertas',
        verbose_name='Entrada',
    )
    tipo = models.CharField(
        max_length=40, choices=TIPO_CHOICES,
        verbose_name='Tipo de alerta',
    )
    severidad = models.CharField(
        max_length=10, choices=SEVERIDAD_CHOICES, default='leve',
        verbose_name='Severidad',
    )
    mensaje = models.TextField(verbose_name='Mensaje')
    activa = models.BooleanField(default=True, verbose_name='Activa')
    resuelta_en = models.DateTimeField(
        null=True, blank=True,
        verbose_name='Resuelta en',
    )
    resuelta_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='+',
        verbose_name='Resuelta por',
    )

    class Meta:
        verbose_name = 'Alerta'
        verbose_name_plural = 'Alertas'
        ordering = ['-creado_at']
        indexes = [
            models.Index(fields=['activa', 'tipo']),
            models.Index(fields=['severidad']),
        ]

    def __str__(self):
        return f'[{self.get_severidad_display()}] {self.get_tipo_display()}'


class UmbralConfiguracion(TimeStampedModel):
    """Configuracion de umbrales para generacion automatica de alertas"""

    TIPO_CHOICES = [
        ('ejecucion_fisica_baja', 'Ejecucion fisica baja'),
        ('ejecucion_financiera_baja', 'Ejecucion financiera baja'),
        ('avance_sin_financiera', 'Avance sin financiamiento'),
        ('financiera_sin_avance', 'Financiamiento sin avance'),
        ('sobreejecucion', 'Sobreejecucion'),
        ('meta_vencida', 'Meta vencida'),
        ('sin_evidencia', 'Sin evidencia'),
        ('incumplimiento_correctivo', 'Incumplimiento de accion correctiva'),
        ('presupuesto_sin_actividad', 'Presupuesto sin actividad'),
        ('actividad_sin_presupuesto', 'Actividad sin presupuesto'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tipo_umbral = models.CharField(
        max_length=40, choices=TIPO_CHOICES, unique=True,
        verbose_name='Tipo de umbral',
    )
    porcentaje_minimo = models.DecimalField(
        max_digits=7, decimal_places=2, default=0,
        verbose_name='Porcentaje minimo',
    )
    porcentaje_maximo = models.DecimalField(
        max_digits=7, decimal_places=2, default=100,
        verbose_name='Porcentaje maximo',
    )
    activo = models.BooleanField(default=True, verbose_name='Activo')
    descripcion = models.TextField(blank=True, default='', verbose_name='Descripcion')

    class Meta:
        verbose_name = 'Umbral de configuracion'
        verbose_name_plural = 'Umbrales de configuracion'
        ordering = ['tipo_umbral']

    def __str__(self):
        return f'{self.get_tipo_umbral_display()} [{self.porcentaje_minimo}% - {self.porcentaje_maximo}%]'
