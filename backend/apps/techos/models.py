import uuid
from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
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

    Desde S2 el techo es 1:1 con una GestionFiscal (R2.1). `gestion` se
    conserva por compatibilidad V1/consolidacion; `clean()` valida que
    coincida con `gestion_fiscal.anio`. `monto_total` queda como columna
    legacy read-only (Q1/DD6): la data-migration 0004 lo recalcula como
    SUM(RecursoTecho.monto) y toda consulta deriva de `total_recursos`.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    gestion = models.PositiveIntegerField()
    gestion_fiscal = models.OneToOneField(
        'gestion.GestionFiscal', on_delete=models.PROTECT,
        related_name='techo', verbose_name='Gestión fiscal',
    )
    monto_total = models.DecimalField(max_digits=18, decimal_places=2, validators=[MinValueValidator(0)])
    otras_afectaciones = models.DecimalField(
        max_digits=18, decimal_places=2, default=0,
        validators=[MinValueValidator(0)],
        help_text='Afectaciones adicionales al techo (gap §12.3 del design)',
    )
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
        constraints = [
            models.CheckConstraint(
                condition=models.Q(monto_total__gte=0),
                name='ck_techo_monto_total_no_negativo',
            ),
            models.CheckConstraint(
                condition=models.Q(otras_afectaciones__gte=0),
                name='ck_techo_otras_afectaciones_no_negativo',
            ),
        ]

    def __str__(self):
        return f'Techo {self.gestion} - {self.fuente.denominacion}: Bs {self.monto_total}'

    def clean(self):
        super().clean()
        if self.gestion_fiscal_id and self.gestion != self.gestion_fiscal.anio:
            raise ValidationError(
                f'La gestión del techo ({self.gestion}) no coincide con la '
                f'gestión fiscal asociada ({self.gestion_fiscal.anio}).'
            )

    @property
    def total_recursos(self):
        """Σ montos de los recursos del techo (calculado, read-only R2.2)."""
        from .services import budget_service
        return budget_service.get_total_recursos(self)

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
    def techo_distribuible(self):
        """techo_distribuible = total_recursos − gastos obligatorios activos
        − otras_afectaciones (calculado, read-only R2.2)."""
        from .services import budget_service
        return budget_service.get_techo_distribuible(self)

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
    monto = models.DecimalField(max_digits=18, decimal_places=2, validators=[MinValueValidator(0)])
    orden = models.PositiveIntegerField(default=0)
    # Campos SIGEP completos (S2, R2.4) — opcionales para compatibilidad V1.
    da = models.ForeignKey(
        DireccionAdministrativa, on_delete=models.PROTECT, null=True, blank=True,
        related_name='recursos_techo',
    )
    ue = models.ForeignKey(
        UnidadEjecutora, on_delete=models.PROTECT, null=True, blank=True,
        related_name='recursos_techo',
    )
    programa = models.ForeignKey(
        'presupuesto.ProgramaPresupuestario', on_delete=models.PROTECT,
        null=True, blank=True, related_name='recursos_techo',
    )
    proyecto = models.ForeignKey(
        'presupuesto.ProyectoPresupuestario', on_delete=models.PROTECT,
        null=True, blank=True, related_name='recursos_techo',
    )
    actividad = models.ForeignKey(
        'presupuesto.ActividadPresupuestaria', on_delete=models.PROTECT,
        null=True, blank=True, related_name='recursos_techo',
    )
    objeto_gasto = models.ForeignKey(
        ObjetoGasto, on_delete=models.PROTECT, null=True, blank=True,
        related_name='recursos_techo',
    )

    class Meta:
        verbose_name = 'Recurso del techo'
        verbose_name_plural = 'Recursos del techo'
        ordering = ['techo', 'orden']
        constraints = [
            models.CheckConstraint(
                condition=models.Q(monto__gte=0),
                name='ck_recurso_techo_monto_no_negativo',
            ),
        ]

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
    proyecto = models.ForeignKey(
        'presupuesto.ProyectoPresupuestario', on_delete=models.PROTECT,
        null=True, blank=True, related_name='gastos_obligatorios_techo',
    )
    actividad = models.ForeignKey(
        'presupuesto.ActividadPresupuestaria', on_delete=models.PROTECT,
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
    monto = models.DecimalField(max_digits=18, decimal_places=2, validators=[MinValueValidator(0)])
    activo = models.BooleanField(default=True)
    orden = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = 'Gasto obligatorio'
        verbose_name_plural = 'Gastos obligatorios'
        ordering = ['techo', 'orden']
        constraints = [
            models.CheckConstraint(
                condition=models.Q(monto__gte=0),
                name='ck_gasto_obligatorio_monto_no_negativo',
            ),
        ]

    def __str__(self):
        return f'{self.techo.gestion} — {self.denominacion}: Bs {self.monto}'


class TechoRecursoGrupo(TimeStampedModel):
    """Grupo jerárquico de recursos por FF/OF (R2.5).

    Agrupa los RecursoTecho del techo por (fuente, organismo). La
    conciliación compara Σ(TechoRecursoDetalle) contra `monto`: sin
    detalles → PENDIENTE; |Σdetalles − monto| == 0 → CONCILIADO;
    |diferencia| > 0 → CON_DIFERENCIA (Q2, sin umbral de silencio).
    `estado_conciliacion`, `diferencia` y `sin_clasificar` son calculados
    por el motor (nunca columnas).
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    techo = models.ForeignKey(
        TechoPresupuestario, on_delete=models.PROTECT, related_name='grupos_recursos',
    )
    fuente = models.ForeignKey(
        FuenteFinanciamiento, on_delete=models.PROTECT, related_name='grupos_recursos_techo',
    )
    organismo = models.ForeignKey(
        OrganismoFinanciador, on_delete=models.PROTECT, null=True, blank=True,
        related_name='grupos_recursos_techo',
    )
    monto = models.DecimalField(max_digits=18, decimal_places=2, validators=[MinValueValidator(0)])
    monto_corriente = models.DecimalField(max_digits=18, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    monto_inversion = models.DecimalField(max_digits=18, decimal_places=2, default=0, validators=[MinValueValidator(0)])

    class Meta:
        verbose_name = 'Grupo de recursos del techo'
        verbose_name_plural = 'Grupos de recursos del techo'
        ordering = ['techo', 'fuente__codigo', 'organismo__codigo']
        indexes = [
            models.Index(fields=['techo']),
            models.Index(fields=['fuente']),
            models.Index(fields=['organismo']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['techo', 'fuente', 'organismo'],
                name='uniq_grupo_recursos_techo_fuente_organismo',
                nulls_distinct=False,
            ),
            models.CheckConstraint(
                condition=models.Q(monto__gte=0),
                name='ck_grupo_recursos_monto_no_negativo',
            ),
            models.CheckConstraint(
                condition=models.Q(monto_corriente__gte=0),
                name='ck_grupo_recursos_corriente_no_negativo',
            ),
            models.CheckConstraint(
                condition=models.Q(monto_inversion__gte=0),
                name='ck_grupo_recursos_inversion_no_negativo',
            ),
        ]

    def __str__(self):
        return f'Grupo {self.techo.gestion} — {self.fuente.codigo}: Bs {self.monto}'


class TechoRecursoDetalle(TimeStampedModel):
    """Detalle (recurso individual) dentro de un TechoRecursoGrupo."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    grupo = models.ForeignKey(
        TechoRecursoGrupo, on_delete=models.CASCADE, related_name='detalles',
    )
    rubro = models.CharField(max_length=20, blank=True, default='')
    concepto = models.CharField(max_length=300)
    monto = models.DecimalField(max_digits=18, decimal_places=2, validators=[MinValueValidator(0)])

    class Meta:
        verbose_name = 'Detalle de recurso del techo'
        verbose_name_plural = 'Detalles de recursos del techo'
        ordering = ['grupo', 'rubro']
        indexes = [
            models.Index(fields=['grupo']),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(monto__gte=0),
                name='ck_detalle_recursos_monto_no_negativo',
            ),
        ]

    def __str__(self):
        return f'{self.concepto}: Bs {self.monto}'


class BolsaPresupuestaria(TimeStampedModel):
    """Bolsa por FF/OF + tipo de gasto (R3.1).

    monto_inicial y monto_ajustes son inputs persistidos; monto_vigente
    (= inicial + ajustes) solo lo escribe el servicio en la misma
    transacción del ajuste (DD2). monto_reservado solo lo escribe el
    servicio bajo lock. monto_distribuido, saldo_disponible y estado son
    calculados (DD1/DD3).

    Unique con nulls_distinct=False (C4): con organismo NULL, dos filas
    se consideran iguales y la unicidad se aplica de verdad (PG15+).
    """
    class TipoGasto(models.TextChoices):
        CORRIENTE = 'CORRIENTE', 'Corriente'
        INVERSION = 'INVERSION', 'Inversión'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    techo = models.ForeignKey(
        TechoPresupuestario, on_delete=models.PROTECT, related_name='bolsas',
    )
    fuente = models.ForeignKey(
        FuenteFinanciamiento, on_delete=models.PROTECT, related_name='bolsas_techo',
    )
    organismo = models.ForeignKey(
        OrganismoFinanciador, on_delete=models.PROTECT, null=True, blank=True,
        related_name='bolsas_techo',
    )
    tipo_gasto = models.CharField(max_length=10, choices=TipoGasto, default=TipoGasto.CORRIENTE)
    monto_inicial = models.DecimalField(max_digits=18, decimal_places=2, validators=[MinValueValidator(0)])
    monto_ajustes = models.DecimalField(
        max_digits=18, decimal_places=2, default=0,
        help_text='Puede ser negativo (REDUCCION); solo lo escribe el servicio',
    )
    monto_vigente = models.DecimalField(
        max_digits=18, decimal_places=2, validators=[MinValueValidator(0)],
        help_text='= monto_inicial + monto_ajustes (C8); solo lo escribe el servicio',
    )
    monto_reservado = models.DecimalField(
        max_digits=18, decimal_places=2, default=0, validators=[MinValueValidator(0)],
        help_text='Solo lo escribe el servicio bajo lock',
    )

    class Meta:
        verbose_name = 'Bolsa presupuestaria'
        verbose_name_plural = 'Bolsas presupuestarias'
        ordering = ['techo', 'fuente__codigo', 'organismo__codigo', 'tipo_gasto']
        indexes = [
            models.Index(fields=['techo']),
            models.Index(fields=['fuente']),
            models.Index(fields=['organismo']),
            models.Index(fields=['tipo_gasto']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['techo', 'fuente', 'organismo', 'tipo_gasto'],
                name='uniq_bolsa_techo_fuente_organismo_tipo_gasto',
                nulls_distinct=False,
            ),
            models.CheckConstraint(
                condition=models.Q(monto_inicial__gte=0),
                name='ck_bolsa_inicial_no_negativo',
            ),
            models.CheckConstraint(
                condition=models.Q(monto_vigente__gte=0),
                name='ck_bolsa_vigente_no_negativo',
            ),
            models.CheckConstraint(
                condition=models.Q(monto_reservado__gte=0),
                name='ck_bolsa_reservado_no_negativo',
            ),
            # C8: monto_vigente = monto_inicial + monto_ajustes.
            models.CheckConstraint(
                condition=models.Q(monto_vigente=models.F('monto_inicial') + models.F('monto_ajustes')),
                name='ck_bolsa_vigente_igual_inicial_mas_ajustes',
            ),
        ]

    def __str__(self):
        return f'Bolsa {self.techo.gestion} — {self.fuente.codigo}/{self.tipo_gasto}: Bs {self.monto_vigente}'


class DistribucionTecho(TimeStampedModel):
    """
    Distribución del techo a nivel de DA/UE/Unidad/Programa/Fuente/Organismo.

    Jerárquica desde S2 (A7): niveles bolsa → CategoriaProgramatica →
    UnidadOrganizacional. La bolsa es la raíz implícita (sin fila); una
    fila de nivel categoría tiene `bolsa` y `categoria_programatica` con
    `padre` null; una hoja tiene `unidad` y `padre` = fila categoría.
    Invariante SUM(hijos) ≤ padre (R4.2) validado en el motor; `clean()`
    es red de seguridad, no barrera de concurrencia (D7).
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    techo = models.ForeignKey(TechoPresupuestario, on_delete=models.CASCADE, related_name='distribuciones')
    padre = models.ForeignKey(
        'self', on_delete=models.PROTECT, null=True, blank=True,
        related_name='hijos',
    )
    bolsa = models.ForeignKey(
        BolsaPresupuestaria, on_delete=models.PROTECT, null=True, blank=True,
        related_name='distribuciones',
    )
    categoria_programatica = models.ForeignKey(
        'presupuesto.CategoriaProgramatica', on_delete=models.PROTECT,
        null=True, blank=True, related_name='distribuciones_techo',
    )
    da = models.ForeignKey(DireccionAdministrativa, on_delete=models.PROTECT, null=True, blank=True, related_name='distribuciones_techo')
    ue = models.ForeignKey(UnidadEjecutora, on_delete=models.PROTECT, null=True, blank=True, related_name='distribuciones_techo')
    unidad = models.ForeignKey(UnidadOrganizacional, on_delete=models.PROTECT, null=True, blank=True, related_name='distribuciones_techo')
    programa = models.ForeignKey(
        'presupuesto.ProgramaPresupuestario', on_delete=models.PROTECT,
        null=True, blank=True, related_name='distribuciones_techo'
    )
    monto_asignado = models.DecimalField(max_digits=18, decimal_places=2, validators=[MinValueValidator(0)])
    monto_reserva = models.DecimalField(max_digits=18, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    activo = models.BooleanField(default=True)
    version = models.PositiveIntegerField(default=1)

    class Meta:
        verbose_name = 'Distribución de techo'
        verbose_name_plural = 'Distribuciones de techo'
        ordering = ['techo', 'da', 'ue']
        indexes = [
            models.Index(fields=['techo']),
            models.Index(fields=['padre']),
            models.Index(fields=['bolsa']),
            models.Index(fields=['categoria_programatica']),
            models.Index(fields=['unidad']),
            models.Index(fields=['techo', 'unidad']),
            models.Index(fields=['techo', 'programa']),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(monto_asignado__gte=0),
                name='ck_distribucion_asignado_no_negativo',
            ),
            models.CheckConstraint(
                condition=models.Q(monto_reserva__gte=0),
                name='ck_distribucion_reserva_no_negativo',
            ),
        ]

    def __str__(self):
        return f'Distribución {self.techo.gestion}: Bs {self.monto_asignado}'

    def clean(self):
        from django.core.exceptions import ValidationError as VE
        from .services import budget_service

        # Red de seguridad del modelo; la barrera de concurrencia real
        # (locks/ledger) llega en S3.
        #
        # 1) Guardia a nivel techo (C3) vía el motor único (D11): misma
        #    ecuación que validate_allocation, que resta el reservado total
        #    y excluye la fila editada leyendo su monto viejo de BD.
        # 2) SUM(hijos) ≤ padre (R4.2): si la fila tiene padre, su monto más
        #    el de los hermanos activos no puede exceder el del padre.
        resultado = budget_service.validate_allocation(
            self.techo,
            self.monto_asignado,
            exclude_id=None if self._state.adding else self.pk,
            monto_reserva_nuevo=self.monto_reserva,
        )
        if not resultado['valido']:
            raise VE(resultado['mensaje'])

        if self.padre_id and self.padre_id != self.pk:
            padre = self.padre
            suma_hijos = budget_service.get_sum_hijos(padre)
            if not self._state.adding and self.activo:
                # Edición: la fila ya está contada en BD con su monto viejo.
                viejo = (
                    DistribucionTecho.objects.filter(pk=self.pk)
                    .values_list('monto_asignado', flat=True)
                    .first()
                )
                if viejo is not None:
                    suma_hijos -= viejo
            if suma_hijos + self.monto_asignado > padre.monto_asignado:
                raise VE(
                    f'La distribución Bs {self.monto_asignado} excede el '
                    f'monto del nodo padre Bs {padre.monto_asignado} '
                    f'(Σ hijos activos Bs {suma_hijos}).'
                )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class AjustePresupuestario(TimeStampedModel):
    """Ajuste de bolsa/techo (S2; los mutantes llegan en S3).

    Cada fila produce su(s) movimiento(s) de ledger. `tipo` puede ser
    INCREMENTO/REDUCCION/RECLASIFICACION; `estado` PENDIENTE/APLICADO/
    RECHAZADO.
    """
    class Tipo(models.TextChoices):
        INCREMENTO = 'INCREMENTO', 'Incremento'
        REDUCCION = 'REDUCCION', 'Reducción'
        RECLASIFICACION = 'RECLASIFICACION', 'Reclasificación'

    class Estado(models.TextChoices):
        PENDIENTE = 'PENDIENTE', 'Pendiente'
        APLICADO = 'APLICADO', 'Aplicado'
        RECHAZADO = 'RECHAZADO', 'Rechazado'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    techo = models.ForeignKey(
        TechoPresupuestario, on_delete=models.PROTECT, related_name='ajustes',
    )
    bolsa = models.ForeignKey(
        BolsaPresupuestaria, on_delete=models.PROTECT, null=True, blank=True,
        related_name='ajustes',
    )
    tipo = models.CharField(max_length=15, choices=Tipo)
    monto = models.DecimalField(max_digits=18, decimal_places=2)
    motivo = models.TextField(blank=True, default='')
    documento = models.CharField(max_length=200, blank=True, default='')
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='ajustes_presupuestarios',
    )
    estado = models.CharField(max_length=10, choices=Estado, default=Estado.PENDIENTE)
    fecha = models.DateTimeField()

    class Meta:
        verbose_name = 'Ajuste presupuestario'
        verbose_name_plural = 'Ajustes presupuestarios'
        ordering = ['-fecha']
        indexes = [
            models.Index(fields=['techo']),
            models.Index(fields=['bolsa']),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(monto__gt=0),
                name='ck_ajuste_monto_positivo',
            ),
        ]

    def __str__(self):
        return f'Ajuste {self.get_tipo_display()} {self.techo.gestion}: Bs {self.monto}'


class MovimientoPresupuestario(TimeStampedModel):
    """Ledger inmutable del núcleo (R6.1).

    Registra cada mutación de saldo (8 tipos) con saldo_antes/después,
    usuario, justificación, documento y fecha. `prev` encadena la
    secuencia por techo para el checksum (DD5, S3). Inmutable (C7):
    save() solo en creación (`self._state.adding`) y delete() lanza
    DomainError; las correcciones van por REVERSION o compensatorio.
    """
    class TipoMovimiento(models.TextChoices):
        DISTRIBUCION = 'DISTRIBUCION', 'Distribución'
        RESERVA = 'RESERVA', 'Reserva'
        LIBERACION = 'LIBERACION', 'Liberación'
        REDISTRIBUCION = 'REDISTRIBUCION', 'Redistribución'
        REVERSION = 'REVERSION', 'Reversión'
        INCREMENTO = 'INCREMENTO', 'Incremento'
        REDUCCION = 'REDUCCION', 'Reducción'
        AJUSTE = 'AJUSTE', 'Ajuste'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    techo = models.ForeignKey(
        TechoPresupuestario, on_delete=models.PROTECT,
        related_name='movimientos_presupuestarios',
    )
    bolsa = models.ForeignKey(
        BolsaPresupuestaria, on_delete=models.PROTECT, null=True, blank=True,
        related_name='movimientos_presupuestarios',
    )
    distribucion = models.ForeignKey(
        DistribucionTecho, on_delete=models.PROTECT, null=True, blank=True,
        related_name='movimientos_presupuestarios',
    )
    tipo = models.CharField(max_length=15, choices=TipoMovimiento)
    monto = models.DecimalField(max_digits=18, decimal_places=2)
    saldo_antes = models.DecimalField(max_digits=18, decimal_places=2)
    saldo_despues = models.DecimalField(max_digits=18, decimal_places=2)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='movimientos_presupuestarios',
    )
    justificacion = models.TextField()
    documento = models.CharField(max_length=200, blank=True, default='')
    fecha = models.DateTimeField()
    prev = models.ForeignKey(
        'self', on_delete=models.PROTECT, null=True, blank=True,
        related_name='siguiente',
    )
    checksum = models.CharField(max_length=64, blank=True, default='')
    reversa_de = models.ForeignKey(
        'self', on_delete=models.PROTECT, null=True, blank=True,
        related_name='reversiones',
    )

    class Meta:
        verbose_name = 'Movimiento presupuestario'
        verbose_name_plural = 'Movimientos presupuestarios'
        ordering = ['-fecha']
        indexes = [
            models.Index(fields=['techo', 'tipo']),
            models.Index(fields=['fecha']),
            models.Index(fields=['bolsa']),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(monto__gt=0),
                name='ck_movimiento_monto_positivo',
            ),
        ]

    def __str__(self):
        return f'{self.get_tipo_display()} {self.techo.gestion}: Bs {self.monto}'

    def save(self, *args, **kwargs):
        # C7: el ledger es inmutable; solo se permite la creación. Con pk
        # UUID por defecto, self.pk siempre es truthy en instancias nuevas,
        # por lo que la guarda correcta es self._state.adding.
        if not self._state.adding:
            from apps.core.exceptions import DomainError
            raise DomainError(
                'El MovimientoPresupuestario es inmutable: no se puede '
                'modificar un movimiento ya registrado.'
            )
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        from apps.core.exceptions import DomainError
        raise DomainError(
            'El MovimientoPresupuestario es inmutable: no se puede eliminar '
            'un movimiento; use REVERSION o un movimiento compensatorio.'
        )


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
