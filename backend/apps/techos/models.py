import uuid
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from apps.core.models import TimeStampedModel
from apps.catalogos.models import FuenteFinanciamiento, OrganismoFinanciador, ObjetoGasto
from apps.organizacion.models import DireccionAdministrativa, UnidadEjecutora, UnidadOrganizacional


class TechoPresupuestario(TimeStampedModel):
    """
    Techo municipal por gestión. Parámetro madre del año fiscal.

    Un techo se compone de recursos (ingresos por fuente/organismo/concepto)
    y de gastos obligatorios reservados (Renta Dignidad, Discapacidad, etc.).
    La distribución por categorías programáticas no puede exceder el saldo
    disponible: monto_total - reservas_gastos_obligatorios - distribuido.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    gestion = models.PositiveIntegerField()
    monto_total = models.DecimalField(max_digits=20, decimal_places=2, validators=[MinValueValidator(0)])
    fuente = models.ForeignKey(FuenteFinanciamiento, on_delete=models.PROTECT, related_name='techos')
    organismo = models.ForeignKey(OrganismoFinanciador, on_delete=models.PROTECT, null=True, blank=True, related_name='techos')
    concepto = models.CharField(max_length=300, blank=True, default='')
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

    @property
    def total_recursos(self):
        return sum(r.monto for r in self.recursos.all())

    @property
    def total_gastos_obligatorios(self):
        """Σ montos de los gastos obligatorios ACTIVOS del techo.

        Delega en el BudgetAllocationService (motor único, D11): la
        ecuación canónica filtra activo=True (misma fuente que
        get_techo_distribuible/saldo_disponible). Sumar la queryset sin
        filtro divergía del motor al desactivar un GastoObligatorio.
        """
        from .services import budget_service
        return budget_service.get_total_gastos_obligatorios(self)

    @property
    def monto_distribuido(self):
        return sum(d.monto_asignado for d in self.distribuciones.filter(activo=True))

    @property
    def saldo_disponible(self):
        """Saldo distribuible: techo - gastos obligatorios - ya distribuido.

        Delega en el BudgetAllocationService (motor único, D11): la ecuación
        canónica usa gastos obligatorios ACTIVOS, consistente con
        resumen_techo/get_techo_resumen.
        """
        from .services import budget_service
        return budget_service.get_available(self)


class RecursoTecho(TimeStampedModel):
    """Ingreso que compone el techo: rubro/fuente/organismo/concepto/monto."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    techo = models.ForeignKey(
        TechoPresupuestario, on_delete=models.CASCADE, related_name='recursos',
    )
    rubro = models.CharField(max_length=20, blank=True, default='')
    rubro_descripcion = models.CharField(max_length=200, blank=True, default='')
    fuente = models.ForeignKey(
        FuenteFinanciamiento, on_delete=models.PROTECT, related_name='recursos_techo',
    )
    organismo = models.ForeignKey(
        OrganismoFinanciador, on_delete=models.PROTECT, null=True, blank=True,
        related_name='recursos_techo',
    )
    entidad_otorgante = models.CharField(max_length=200, blank=True, default='')
    concepto = models.CharField(max_length=300)
    monto = models.DecimalField(max_digits=20, decimal_places=2, validators=[MinValueValidator(0)])
    orden = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = 'Recurso del techo'
        verbose_name_plural = 'Recursos del techo'
        ordering = ['techo', 'orden']

    def __str__(self):
        return f'{self.techo.gestion} — {self.concepto}: Bs {self.monto}'


class GastoObligatorio(TimeStampedModel):
    """Reserva obligatoria que se descuenta del techo antes de distribuir."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    techo = models.ForeignKey(
        TechoPresupuestario, on_delete=models.CASCADE, related_name='gastos_obligatorios',
    )
    da = models.ForeignKey(
        DireccionAdministrativa, on_delete=models.PROTECT, null=True, blank=True,
        related_name='gastos_obligatorios_techo',
    )
    ue = models.ForeignKey(
        UnidadEjecutora, on_delete=models.PROTECT, null=True, blank=True,
        related_name='gastos_obligatorios_techo',
    )
    programa = models.ForeignKey(
        'presupuesto.ProgramaPresupuestario', on_delete=models.PROTECT,
        null=True, blank=True, related_name='gastos_obligatorios_techo',
    )
    fuente = models.ForeignKey(
        FuenteFinanciamiento, on_delete=models.PROTECT,
        related_name='gastos_obligatorios_techo',
    )
    organismo = models.ForeignKey(
        OrganismoFinanciador, on_delete=models.PROTECT, null=True, blank=True,
        related_name='gastos_obligatorios_techo',
    )
    objeto_gasto = models.ForeignKey(
        ObjetoGasto, on_delete=models.PROTECT, null=True, blank=True,
        related_name='gastos_obligatorios_techo',
    )
    denominacion = models.CharField(max_length=300)
    base_legal = models.CharField(max_length=200, blank=True, default='')
    monto = models.DecimalField(max_digits=20, decimal_places=2, validators=[MinValueValidator(0)])
    activo = models.BooleanField(default=True)
    orden = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = 'Gasto obligatorio'
        verbose_name_plural = 'Gastos obligatorios'
        ordering = ['techo', 'orden']

    def __str__(self):
        return f'{self.techo.gestion} — {self.denominacion}: Bs {self.monto}'


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

    def clean(self):
        from django.core.exceptions import ValidationError as VE
        from .services import budget_service

        # Guardia a nivel techo (C3) vía el motor único (D11): misma
        # ecuación que validate_allocation, que resta el reservado total
        # (W4) y excluye la fila editada leyendo su monto viejo de BD
        # (W3: Decimal('0.00') es falsy, por eso no se usa 'or self.monto').
        # Red de seguridad del modelo; la barrera de concurrencia real
        # (locks/ledger) llega en S3.
        resultado = budget_service.validate_allocation(
            self.techo,
            self.monto_asignado,
            exclude_id=None if self._state.adding else self.pk,
        )
        if not resultado['valido']:
            raise VE(resultado['mensaje'])

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


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
