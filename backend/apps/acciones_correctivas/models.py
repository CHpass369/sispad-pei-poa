import uuid
from django.db import models
from django.conf import settings
from apps.core.models import TimeStampedModel


class AccionCorrectiva(TimeStampedModel):

    class Estado(models.TextChoices):
        PENDIENTE = 'pendiente', 'Pendiente'
        EN_EJECUCION = 'en_ejecucion', 'En Ejecución'
        CUMPLIDA = 'cumplida', 'Cumplida'
        INCUMPLIDA = 'incumplida', 'Incumplida'
        CERRADA = 'cerrada', 'Cerrada'
        CANCELADA = 'cancelada', 'Cancelada'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    alerta = models.ForeignKey(
        'seguimiento.Alerta', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='acciones_correctivas',
        verbose_name='Alerta',
    )
    entry = models.ForeignKey(
        'seguimiento.EntradaSeguimiento', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='acciones_correctivas',
        verbose_name='Entrada de Seguimiento',
    )
    description = models.TextField(verbose_name='Descripción')
    cause = models.TextField(verbose_name='Causa')
    responsible = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='acciones_correctivas',
        verbose_name='Responsable',
    )
    responsible_unit = models.ForeignKey(
        'organizacion.UnidadOrganizacional', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='acciones_correctivas',
        verbose_name='Unidad Responsable',
    )
    start_date = models.DateField(verbose_name='Fecha de Inicio')
    due_date = models.DateField(verbose_name='Fecha Límite')
    expected_result = models.TextField(verbose_name='Resultado Esperado')
    status = models.CharField(
        max_length=20, choices=Estado, default=Estado.PENDIENTE,
        verbose_name='Estado',
    )
    evidence = models.TextField(
        blank=True, null=True, verbose_name='Evidencia',
    )
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='acciones_verificadas',
        verbose_name='Verificado por',
    )
    verified_at = models.DateTimeField(
        null=True, blank=True, verbose_name='Fecha de Verificación',
    )
    gestion = models.PositiveIntegerField(verbose_name='Gestión')

    class Meta:
        verbose_name = 'Acción Correctiva'
        verbose_name_plural = 'Acciones Correctivas'
        ordering = ['-gestion', 'status', 'due_date']
        indexes = [
            models.Index(fields=['gestion', 'status']),
            models.Index(fields=['due_date']),
            models.Index(fields=['responsible']),
        ]

    def __str__(self):
        return f'AC-{self.pk} - {self.description[:60]}'

    @property
    def esta_vencida(self):
        from django.utils import timezone
        return (
            self.status in (self.Estado.PENDIENTE, self.Estado.EN_EJECUCION)
            and self.due_date < timezone.now().date()
        )

    @property
    def porcentaje_cumplimiento(self):
        total = self.compromisos.count()
        if total == 0:
            return 0
        cumplidos = self.compromisos.filter(status='cumplido').count()
        return round((cumplidos / total) * 100, 2)


class CompromisoAccionCorrectiva(TimeStampedModel):

    class Estado(models.TextChoices):
        PENDIENTE = 'pendiente', 'Pendiente'
        CUMPLIDO = 'cumplido', 'Cumplido'
        INCUMPLIDO = 'incumplido', 'Incumplido'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    accion_correctiva = models.ForeignKey(
        AccionCorrectiva, on_delete=models.CASCADE,
        related_name='compromisos',
        verbose_name='Acción Correctiva',
    )
    description = models.TextField(verbose_name='Descripción')
    due_date = models.DateField(verbose_name='Fecha Límite')
    status = models.CharField(
        max_length=20, choices=Estado, default=Estado.PENDIENTE,
        verbose_name='Estado',
    )
    completed_at = models.DateTimeField(
        null=True, blank=True, verbose_name='Fecha de Cumplimiento',
    )
    notes = models.TextField(blank=True, verbose_name='Notas')

    class Meta:
        verbose_name = 'Compromiso de Acción Correctiva'
        verbose_name_plural = 'Compromisos de Acciones Correctivas'
        ordering = ['due_date', 'status']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['due_date']),
        ]

    def __str__(self):
        return f'{self.accion_correctiva_id} - {self.description[:60]}'

    @property
    def esta_vencido(self):
        from django.utils import timezone
        return (
            self.status == self.Estado.PENDIENTE
            and self.due_date < timezone.now().date()
        )
