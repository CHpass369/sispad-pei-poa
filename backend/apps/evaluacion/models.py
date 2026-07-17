import uuid
from django.db import models
from django.conf import settings
from apps.core.models import TimeStampedModel


class Evaluacion(TimeStampedModel):
    TIPO_EVALUACION_CHOICES = [
        ('anual', 'Anual'),
        ('medio_termino', 'Medio Término'),
        ('final', 'Final'),
        ('especifica', 'Específica'),
    ]

    ESTADO_CHOICES = [
        ('borrador', 'Borrador'),
        ('en_curso', 'En Curso'),
        ('completada', 'Completada'),
        ('aprobada', 'Aprobada'),
    ]

    PERIODO_CHOICES = [
        ('Q1', 'Primer Trimestre'),
        ('Q2', 'Segundo Trimestre'),
        ('Q3', 'Tercer Trimestre'),
        ('Q4', 'Cuarto Trimestre'),
        ('S1', 'Primer Semestre'),
        ('S2', 'Segundo Semestre'),
        ('AN', 'Anual'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    plan = models.ForeignKey(
        'planificacion.Plan', on_delete=models.PROTECT,
        related_name='evaluaciones',
        verbose_name='Plan',
    )
    fiscal_year = models.PositiveIntegerField(verbose_name='Gestión')
    evaluation_type = models.CharField(
        max_length=20, choices=TIPO_EVALUACION_CHOICES,
        verbose_name='Tipo de Evaluación',
    )
    period = models.CharField(
        max_length=2, choices=PERIODO_CHOICES, default='AN',
        verbose_name='Período',
    )
    responsible_team = models.TextField(
        blank=True, verbose_name='Equipo Responsable',
        help_text='Nombres del equipo encargado de la evaluación',
    )
    status = models.CharField(
        max_length=20, choices=ESTADO_CHOICES, default='borrador',
        verbose_name='Estado',
    )
    conclusions = models.TextField(blank=True, verbose_name='Conclusiones')
    recommendations = models.TextField(blank=True, verbose_name='Recomendaciones Generales')
    approved_document = models.FileField(
        upload_to='evaluaciones/aprobados/%Y/',
        null=True, blank=True, verbose_name='Documento Aprobado',
    )

    class Meta:
        verbose_name = 'Evaluación'
        verbose_name_plural = 'Evaluaciones'
        ordering = ['-fiscal_year', 'evaluation_type']
        unique_together = [('plan', 'fiscal_year', 'evaluation_type', 'period')]
        indexes = [
            models.Index(fields=['fiscal_year', 'evaluation_type']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return (
            f'{self.get_evaluation_type_display()} {self.fiscal_year} '
            f'- {self.get_period_display()}'
        )


class CriterioEvaluacion(TimeStampedModel):
    CRITERIO_CHOICES = [
        ('eficacia', 'Eficacia'),
        ('eficiencia', 'Eficiencia'),
        ('efectividad', 'Efectividad'),
        ('pertinencia', 'Pertinencia'),
        ('impacto', 'Impacto'),
        ('sostenibilidad', 'Sostenibilidad'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    evaluacion = models.ForeignKey(
        Evaluacion, on_delete=models.CASCADE,
        related_name='criterios',
        verbose_name='Evaluación',
    )
    criterion = models.CharField(
        max_length=20, choices=CRITERIO_CHOICES,
        verbose_name='Criterio',
    )
    score = models.DecimalField(
        max_digits=5, decimal_places=2, default=0,
        verbose_name='Puntaje',
        help_text='Puntaje de 0 a 100',
    )
    weight = models.DecimalField(
        max_digits=5, decimal_places=2, default=0,
        verbose_name='Peso',
        help_text='Peso relativo del criterio (0 a 1)',
    )
    justification = models.TextField(blank=True, verbose_name='Justificación')
    observations = models.TextField(blank=True, verbose_name='Observaciones')

    class Meta:
        verbose_name = 'Criterio de Evaluación'
        verbose_name_plural = 'Criterios de Evaluación'
        unique_together = [('evaluacion', 'criterion')]
        ordering = ['evaluacion', 'criterion']

    def __str__(self):
        return f'{self.get_criterion_display()} - {self.score}'

    @property
    def weighted_score(self):
        return self.score * self.weight


class ResultadoEvaluacion(TimeStampedModel):
    ESTADO_RESULTADO_CHOICES = [
        ('cumple', 'Cumple'),
        ('parcial', 'Cumple Parcialmente'),
        ('no_cumple', 'No Cumple'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    evaluacion = models.ForeignKey(
        Evaluacion, on_delete=models.CASCADE,
        related_name='resultados',
        verbose_name='Evaluación',
    )
    poau = models.ForeignKey(
        'poau.POAU', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='resultados_evaluacion',
        verbose_name='POAU',
    )
    unidad = models.ForeignKey(
        'organizacion.UnidadOrganizacional', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='resultados_evaluacion',
        verbose_name='Unidad Organizacional',
    )
    resultado_pad = models.ForeignKey(
        'pad.ResultadoTerritorial', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='resultados_evaluacion',
        verbose_name='Resultado PAD',
    )
    score_global = models.DecimalField(
        max_digits=5, decimal_places=2, default=0,
        verbose_name='Puntaje Global',
    )
    status = models.CharField(
        max_length=20, choices=ESTADO_RESULTADO_CHOICES, default='parcial',
        verbose_name='Estado',
    )
    observations = models.TextField(blank=True, verbose_name='Observaciones')

    class Meta:
        verbose_name = 'Resultado de Evaluación'
        verbose_name_plural = 'Resultados de Evaluación'
        ordering = ['-score_global']
        indexes = [
            models.Index(fields=['evaluacion', 'status']),
        ]

    def __str__(self):
        target = self.poau or self.unidad or self.resultado_pad or 'Sin referencia'
        return f'{target} - {self.get_status_display()} ({self.score_global})'


class LeccionAprendida(TimeStampedModel):
    CATEGORIA_CHOICES = [
        ('tecnica', 'Técnica'),
        ('organizacional', 'Organizacional'),
        ('financiera', 'Financiera'),
        ('institucional', 'Institucional'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    evaluacion = models.ForeignKey(
        Evaluacion, on_delete=models.CASCADE,
        related_name='lecciones',
        verbose_name='Evaluación',
    )
    title = models.CharField(max_length=300, verbose_name='Título')
    description = models.TextField(verbose_name='Descripción')
    category = models.CharField(
        max_length=20, choices=CATEGORIA_CHOICES,
        verbose_name='Categoría',
    )
    recommendations = models.TextField(blank=True, verbose_name='Recomendaciones')

    class Meta:
        verbose_name = 'Lección Aprendida'
        verbose_name_plural = 'Lecciones Aprendidas'
        ordering = ['category', 'title']

    def __str__(self):
        return f'{self.title} ({self.get_category_display()})'


class Recomendacion(TimeStampedModel):
    PRIORIDAD_CHOICES = [
        ('alta', 'Alta'),
        ('media', 'Media'),
        ('baja', 'Baja'),
    ]

    ESTADO_RECOMENDACION_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('en_proceso', 'En Proceso'),
        ('cumplida', 'Cumplida'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    evaluacion = models.ForeignKey(
        Evaluacion, on_delete=models.CASCADE,
        related_name='recomendaciones',
        verbose_name='Evaluación',
    )
    description = models.TextField(verbose_name='Descripción')
    priority = models.CharField(
        max_length=10, choices=PRIORIDAD_CHOICES, default='media',
        verbose_name='Prioridad',
    )
    responsible_unit = models.CharField(
        max_length=300, blank=True,
        verbose_name='Unidad Responsable',
    )
    status = models.CharField(
        max_length=20, choices=ESTADO_RECOMENDACION_CHOICES, default='pendiente',
        verbose_name='Estado',
    )
    due_date = models.DateField(null=True, blank=True, verbose_name='Fecha Límite')

    class Meta:
        verbose_name = 'Recomendación'
        verbose_name_plural = 'Recomendaciones'
        ordering = ['priority', 'due_date']

    def __str__(self):
        return f'{self.description[:80]} ({self.get_priority_display()})'
