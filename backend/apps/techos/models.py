import uuid
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from apps.core.models import TimeStampedModel
from apps.catalogos.models import FuenteFinanciamiento, OrganismoFinanciador
from apps.organizacion.models import DireccionAdministrativa, UnidadEjecutora, UnidadOrganizacional


class TechoPresupuestario(TimeStampedModel):
    """
    Techo municipal general. Carga inicial de límite presupuestario.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    gestion = models.PositiveIntegerField()
    monto_total = models.DecimalField(max_digits=20, decimal_places=2, validators=[MinValueValidator(0)])
    fuente = models.ForeignKey(FuenteFinanciamiento, on_delete=models.PROTECT, related_name='techos')
    organismo = models.ForeignKey(OrganismoFinanciador, on_delete=models.PROTECT, null=True, blank=True, related_name='techos')
    descripcion = models.TextField(blank=True)
    activo = models.BooleanField(default=True)
    version = models.PositiveIntegerField(default=1)

    class Meta:
        verbose_name = 'Techo presupuestario'
        verbose_name_plural = 'Techos presupuestarios'
        ordering = ['-gestion', 'fuente__codigo']
        indexes = [
            models.Index(fields=['gestion', 'fuente', 'organismo']),
        ]

    def __str__(self):
        return f'Techo {self.gestion} - {self.fuente.denominacion}: Bs {self.monto_total}'


class DistribucionTecho(TimeStampedModel):
    """
    Distribución del techo a nivel de DA/UE/Unidad/Programa/Fuente/Organismo.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    techo = models.ForeignKey(TechoPresupuestario, on_delete=models.CASCADE, related_name='distribuciones')
    da = models.ForeignKey(DireccionAdministrativa, on_delete=models.PROTECT, null=True, blank=True, related_name='distribuciones_techo')
    ue = models.ForeignKey(UnidadEjecutora, on_delete=models.PROTECT, null=True, blank=True, related_name='distribuciones_techo')
    unidad = models.ForeignKey(UnidadOrganizacional, on_delete=models.PROTECT, null=True, blank=True, related_name='distribuciones_techo')
    programa = models.ForeignKey(
        'presupuesto.ProgramaPresupuestario', on_delete=models.PROTECT,
        null=True, blank=True, related_name='distribuciones_techo'
    )
    monto_asignado = models.DecimalField(max_digits=20, decimal_places=2, validators=[MinValueValidator(0)])
    monto_reserva = models.DecimalField(max_digits=20, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    activo = models.BooleanField(default=True)
    version = models.PositiveIntegerField(default=1)

    class Meta:
        verbose_name = 'Distribución de techo'
        verbose_name_plural = 'Distribuciones de techo'
        ordering = ['techo', 'da', 'ue']
        indexes = [
            models.Index(fields=['techo', 'unidad']),
            models.Index(fields=['techo', 'programa']),
        ]

    def __str__(self):
        return f'Distribución {self.techo.gestion}: Bs {self.monto_asignado}'


class MovimientoTecho(TimeStampedModel):
    MOVEMENT_TYPE_CHOICES = [
        ('asignacion', 'Asignación'),
        ('incremento', 'Incremento'),
        ('reduccion', 'Reducción'),
        ('transferencia', 'Transferencia'),
        ('reserva', 'Reserva'),
        ('liberacion', 'Liberación'),
        ('ajuste', 'Ajuste'),
        ('reversion', 'Reversión'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    techo = models.ForeignKey(TechoPresupuestario, on_delete=models.PROTECT, related_name='movimientos')
    movement_type = models.CharField(max_length=20, choices=MOVEMENT_TYPE_CHOICES)
    source_ceiling = models.ForeignKey(
        TechoPresupuestario, on_delete=models.PROTECT,
        null=True, blank=True, related_name='movimientos_origen'
    )
    destination_ceiling = models.ForeignKey(
        TechoPresupuestario, on_delete=models.PROTECT,
        null=True, blank=True, related_name='movimientos_destino'
    )
    amount = models.DecimalField(max_digits=20, decimal_places=2, validators=[MinValueValidator(0)])
    justification = models.TextField()
    document = models.TextField(null=True, blank=True)
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='movimientos_techo_solicitados'
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='movimientos_techo_aprobados'
    )
    date = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Movimiento de techo'
        verbose_name_plural = 'Movimientos de techo'
        ordering = ['-date']
        indexes = [
            models.Index(fields=['techo', 'movement_type']),
            models.Index(fields=['date']),
        ]

    def __str__(self):
        return f'{self.get_movement_type_display()} - {self.techo}: Bs {self.amount}'
