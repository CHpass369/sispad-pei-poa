from decimal import Decimal
from django.db import transaction
from django.db.models import Sum
from .models import DistribucionTecho, MovimientoTecho, TechoPresupuestario


def obtener_saldo_disponible(techo):
    movimientos_aprobados = MovimientoTecho.objects.filter(
        techo=techo,
        approved_by__isnull=False
    )

    saldo = techo.monto_total
    for mov in movimientos_aprobados:
        if mov.movement_type in ('asignacion', 'incremento', 'transferencia', 'ajuste'):
            saldo += mov.amount
        elif mov.movement_type in ('reduccion', 'reserva', 'liberacion', 'reversion'):
            saldo -= mov.amount
    return saldo


def resumen_techo(techo):
    """Resumen de control del techo: totales y saldo para distribución."""
    recursos = techo.recursos.aggregate(total=Sum('monto'))['total'] or Decimal('0')
    gastos_obligatorios = (
        techo.gastos_obligatorios.filter(activo=True)
        .aggregate(total=Sum('monto'))['total'] or Decimal('0')
    )
    distribuido = (
        techo.distribuciones.filter(activo=True)
        .aggregate(total=Sum('monto_asignado'))['total'] or Decimal('0')
    )
    return {
        'techo_id': str(techo.id),
        'gestion': techo.gestion,
        'monto_total': techo.monto_total,
        'total_recursos': recursos,
        'total_gastos_obligatorios': gastos_obligatorios,
        'monto_distribuido': distribuido,
        'saldo_disponible': techo.monto_total - gastos_obligatorios - distribuido,
        'excede': distribuido > (techo.monto_total - gastos_obligatorios),
    }


def validar_distribucion_no_excede(techo, monto_asignado, exclude_id=None):
    """Valida que una distribución no exceda el saldo disponible del techo."""
    distribuido = (
        techo.distribuciones.filter(activo=True)
        .exclude(pk=exclude_id)
        .aggregate(total=Sum('monto_asignado'))['total'] or Decimal('0')
    )
    gastos_obligatorios = (
        techo.gastos_obligatorios.filter(activo=True)
        .aggregate(total=Sum('monto'))['total'] or Decimal('0')
    )
    saldo = techo.monto_total - gastos_obligatorios - distribuido
    return {
        'monto_solicitado': monto_asignado,
        'saldo_disponible': saldo,
        'excede': monto_asignado > saldo,
    }


def validar_movimiento(movimiento):
    errores = []

    if movimiento.amount <= 0:
        errores.append('El monto del movimiento debe ser mayor a cero.')

    if movimiento.movement_type == 'transferencia':
        if not movimiento.source_ceiling:
            errores.append('Para transferencias se requiere un techo origen.')
        if not movimiento.destination_ceiling:
            errores.append('Para transferencias se requiere un techo destino.')
        if (movimiento.source_ceiling and
                movimiento.source_ceiling.id == movimiento.destination_ceiling_id):
            errores.append('El techo origen y destino no pueden ser el mismo.')

    if movimiento.movement_type in ('incremento', 'asignacion', 'transferencia', 'ajuste'):
        if movimiento.source_ceiling:
            saldo_origen = obtener_saldo_disponible(movimiento.source_ceiling)
            if movimiento.amount > saldo_origen:
                errores.append(
                    f'El monto Bs {movimiento.amount} excede el saldo disponible '
                    f'del techo origen Bs {saldo_origen}.'
                )

    return errores


@transaction.atomic
def aplicar_movimiento(movimiento):
    errores = validar_movimiento(movimiento)
    if errores:
        raise ValueError('; '.join(errores))

    movimientos_existentes = MovimientoTecho.objects.filter(
        techo=movimiento.techo,
        approved_by__isnull=False
    ).exclude(pk=movimiento.pk)

    total_movimientos = sum(
        m.amount for m in movimientos_existentes
        if m.movement_type in ('reduccion', 'reserva', 'liberacion', 'reversion')
    )
    total_incrementos = sum(
        m.amount for m in movimientos_existentes
        if m.movement_type in ('asignacion', 'incremento', 'transferencia', 'ajuste')
    )

    nuevo_total = movimiento.techo.monto_total + total_incrementos - total_movimientos
    if movimiento.movement_type in ('reduccion', 'reserva', 'liberacion', 'reversion'):
        if movimiento.amount > nuevo_total:
            raise ValueError(
                f'El monto de reducción Bs {movimiento.amount} excede '
                f'el saldo disponible Bs {nuevo_total}.'
            )

    movimiento.save()
    return movimiento


class BudgetAllocationService:
    """Motor único de asignación presupuestaria (design §3, slice S1).

    Única fuente de verdad para consultas y validación de saldos (gate R7):
    las 6 implementaciones legacy delegan aquí (D11). Las operaciones
    mutantes (allocate/reserve/release/reverse/transfer/ajustar) y los locks
    en cascada se incorporan en el slice S3; este slice es solo consulta y
    validación no mutante, sin locks ni ledger.

    Reglas:
    - Siempre Decimal (NUMERIC(18,2) en BD), nunca float.
    - Agregados SUM en BD (sin N+1).
    - Guardia a nivel techo (C3): Σ activo hojas (bolsas + legacy) +
      reservado_total ≤ techo_distribuible; la capacidad efectiva de una
      bolsa es min(saldo_bolsa, techo_distribuible - Σ hojas - reservado).
    """

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _decimal(valor) -> Decimal:
        """Normaliza a Decimal (NUMERIC(18,2)), nunca float."""
        if valor is None:
            return Decimal('0.00')
        if isinstance(valor, Decimal):
            return valor
        return Decimal(str(valor))

    def _sum(self, qs, campo) -> Decimal:
        """Suma agregada en BD sobre un queryset."""
        return self._decimal(qs.aggregate(total=Sum(campo))['total'])

    def _sum_activo(self, qs, campo) -> Decimal:
        """Suma agregada en BD solo de filas activas."""
        return self._sum(qs.filter(activo=True), campo)

    # ------------------------------------------------------------------
    # Consultas a nivel bolsa (duck-typed: en S1 el techo legacy actúa
    # como bolsa; BolsaPresupuestaria llega en S2)
    # ------------------------------------------------------------------

    def get_amount(self, bolsa) -> Decimal:
        """Monto vigente de la bolsa (monto_vigente, S2). Para el techo
        legacy expone monto_total."""
        if isinstance(bolsa, TechoPresupuestario):
            return self._decimal(bolsa.monto_total)
        return self._decimal(getattr(bolsa, 'monto_vigente', Decimal('0.00')))

    def get_reserved(self, bolsa) -> Decimal:
        """Monto reservado: columna monto_reservado de la bolsa (S2) o
        Σ monto_reserva de las distribuciones activas del techo legacy."""
        if isinstance(bolsa, TechoPresupuestario):
            return self._sum_activo(bolsa.distribuciones, 'monto_reserva')
        return self._decimal(getattr(bolsa, 'monto_reservado', Decimal('0.00')))

    def get_distributed(self, bolsa) -> Decimal:
        """Monto distribuido activo: SUM(DistribucionTecho.activo) de la
        bolsa (S2) o del techo legacy."""
        if isinstance(bolsa, TechoPresupuestario):
            return self._sum_activo(bolsa.distribuciones, 'monto_asignado')
        qs = getattr(bolsa, 'distribuciones', None)
        if qs is None:
            qs = bolsa.distribuciontecho_set.all()
        return self._sum_activo(qs, 'monto_asignado')

    def get_distributed_nodo(self, nodo) -> Decimal:
        """Monto distribuido del nodo: Σ hijos activos si es nodo
        intermedio (jerárquico, S2), o monto_asignado si es hoja
        (esquema actual S1)."""
        hijos = getattr(nodo, 'hijos', None)
        if hijos is not None:
            try:
                qs = hijos.all() if hasattr(hijos, 'all') else hijos
                if qs.exists():
                    return self._sum_activo(qs, 'monto_asignado')
            except (AttributeError, ValueError, TypeError):
                pass
        return self._decimal(nodo.monto_asignado)

    def get_available(self, bolsa) -> Decimal:
        """Saldo disponible: techo distribuible - distribuido (techo) o
        vigente - reservado - distribuido (bolsa, S2)."""
        if isinstance(bolsa, TechoPresupuestario):
            return self.get_techo_distribuible(bolsa) - self.get_distributed(bolsa)
        return self.get_amount(bolsa) - self.get_reserved(bolsa) - self.get_distributed(bolsa)

    # ------------------------------------------------------------------
    # Consultas a nivel techo
    # ------------------------------------------------------------------

    def get_total_recursos(self, techo) -> Decimal:
        """Σ montos de los recursos del techo."""
        return self._sum(techo.recursos.all(), 'monto')

    def get_total_gastos_obligatorios(self, techo) -> Decimal:
        """Σ montos de los gastos obligatorios ACTIVOS del techo."""
        return self._sum_activo(techo.gastos_obligatorios.all(), 'monto')

    def get_techo_distribuible(self, techo) -> Decimal:
        """techo_distribuible = monto_total - gastos obligatorios activos
        - otras_afectaciones (otras_afectaciones llega en S2; la migración
        0004 iguala monto_total con total_recursos)."""
        return (
            self._decimal(techo.monto_total)
            - self.get_total_gastos_obligatorios(techo)
            - self._decimal(getattr(techo, 'otras_afectaciones', Decimal('0.00')))
        )

    def get_techo_resumen(self, techo) -> dict:
        """Resumen unificado del techo (sustituye resumen_techo, D11).

        Mismas claves que el resumen legacy + claves nuevas
        (monto_reservado, techo_distribuible, estado).
        """
        gastos = self.get_total_gastos_obligatorios(techo)
        distribuido = self._sum_activo(techo.distribuciones, 'monto_asignado')
        reservado = self._sum_activo(techo.distribuciones, 'monto_reserva')
        distribuible = self.get_techo_distribuible(techo)
        return {
            'techo_id': str(techo.id),
            'gestion': techo.gestion,
            'monto_total': self._decimal(techo.monto_total),
            'total_recursos': self.get_total_recursos(techo),
            'total_gastos_obligatorios': gastos,
            'monto_distribuido': distribuido,
            'monto_reservado': reservado,
            'techo_distribuible': distribuible,
            'saldo_disponible': distribuible - distribuido,
            'excede': distribuido > distribuible,
            'estado': self.estado_techo(techo),
        }

    def estado_techo(self, techo) -> str:
        """Estado calculado del techo (DD3).

        Precedencia: CERRADO > VIGENTE > INCONSISTENTE >
        DISTRIBUCION_COMPLETA > DISTRIBUCION_PARCIAL > EN_CONFIGURACION >
        SIN_CONFIGURAR. En S1 no existe gestion_fiscal ni bolsas: los
        estados CERRADO/VIGENTE/EN_CONFIGURACION quedan inertes hasta S2.
        """
        gestion = getattr(techo, 'gestion_fiscal', None)
        if gestion is not None:
            operativo = _estado_operativo_gestion(gestion.estado)
            if operativo == 'CERRADA':
                return 'CERRADO'
            if operativo == 'VIGENTE':
                return 'VIGENTE'

        distribuible = self.get_techo_distribuible(techo)
        distribuido = self._sum_activo(techo.distribuciones, 'monto_asignado')
        if distribuido > distribuible:
            return 'INCONSISTENTE'
        if distribuido == distribuible:
            return 'DISTRIBUCION_COMPLETA'
        if distribuido > 0:
            return 'DISTRIBUCION_PARCIAL'
        bolsas = getattr(techo, 'bolsas', None)
        if bolsas is not None and bolsas.exists():
            return 'EN_CONFIGURACION'
        return 'SIN_CONFIGURAR'

    def estado_bolsa(self, bolsa) -> str:
        """Estado calculado de la bolsa (R3.2/DD3).

        CERRADA > BLOQUEADA > TOTALMENTE_DISTRIBUIDA >
        PARCIALMENTE_DISTRIBUIDA > DISPONIBLE. Requiere BolsaPresupuestaria
        (S2); en S1 el techo legacy se evalúa con estado_techo.
        """
        techo = getattr(bolsa, 'techo', None)
        if techo is not None and self.estado_techo(techo) == 'CERRADO':
            return 'CERRADA'
        if isinstance(bolsa, TechoPresupuestario):
            return self.estado_techo(bolsa)
        vigente = self.get_amount(bolsa)
        reservado = self.get_reserved(bolsa)
        distribuido = self.get_distributed(bolsa)
        saldo = self.get_available(bolsa)
        if reservado > 0 and saldo <= 0:
            return 'BLOQUEADA'
        if distribuido == vigente and vigente > 0:
            return 'TOTALMENTE_DISTRIBUIDA'
        if Decimal('0.00') < distribuido < vigente:
            return 'PARCIALMENTE_DISTRIBUIDA'
        return 'DISPONIBLE'

    # ------------------------------------------------------------------
    # Agregados por gestión / programa (compatibilidad consolidación,
    # reportes y validar_techo — D11)
    # ------------------------------------------------------------------

    def get_techo_agregado_gestion(self, gestion) -> Decimal:
        """Σ monto_total de los techos ACTIVOS de una gestión."""
        return self._sum(
            TechoPresupuestario.objects.filter(gestion=gestion, activo=True),
            'monto_total',
        )

    def get_distribuido_agregado_gestion(self, gestion) -> Decimal:
        """Σ monto_asignado de las distribuciones activas de una gestión."""
        return self._sum(
            DistribucionTecho.objects.filter(techo__gestion=gestion, activo=True),
            'monto_asignado',
        )

    def get_saldo_por_distribuir_gestion(self, gestion) -> Decimal:
        """Saldo por distribuir de una gestión: techo agregado - distribuido."""
        return (
            self.get_techo_agregado_gestion(gestion)
            - self.get_distribuido_agregado_gestion(gestion)
        )

    def get_distribuido_por_programa(self, programa) -> Decimal:
        """Σ monto_asignado de las distribuciones activas de un programa
        (reportes)."""
        return self._sum(
            DistribucionTecho.objects.filter(programa=programa, activo=True),
            'monto_asignado',
        )

    def get_saldo_por_movimientos(self, techo) -> Decimal:
        """Saldo por movimientos aprobados (compatibilidad legacy V1, A11).

        No es la ecuación canónica: reproduce la semántica histórica de
        obtener_saldo_disponible (monto_total ± movimientos aprobados)
        para no alterar la salida de los endpoints V1. La ecuación
        canónica vive en get_available/get_techo_resumen.
        """
        saldo = self._decimal(techo.monto_total)
        for mov in MovimientoTecho.objects.filter(
            techo=techo, approved_by__isnull=False
        ):
            if mov.movement_type in ('asignacion', 'incremento', 'transferencia', 'ajuste'):
                saldo += self._decimal(mov.amount)
            elif mov.movement_type in ('reduccion', 'reserva', 'liberacion', 'reversion'):
                saldo -= self._decimal(mov.amount)
        return saldo

    # ------------------------------------------------------------------
    # Validación no mutante (R5.3)
    # ------------------------------------------------------------------

    def can_allocate(self, bolsa, monto, nodo=None) -> bool:
        """¿Se puede asignar `monto` a la bolsa/nodo? (sin mutar)."""
        return self.validate_allocation(
            bolsa, monto, nodo=nodo,
        )['valido']

    def validate_allocation(
        self, bolsa, monto, categoria=None, unidad=None, usuario=None,
        nodo=None, exclude_id=None,
    ) -> dict:
        """Valida una asignación contra la capacidad efectiva (R5.4).

        Capacidad efectiva = min(saldo de la bolsa, techo_distribuible
        - Σ activo hojas - reservado_total) — guardia a nivel techo (C3):
        las bolsas se crean desde Σ recursos y su Σ puede exceder
        techo_distribuible, por lo que la bolsa individual no alcanza a
        ver el exceso. No muta ni adquiere locks (S3).

        Retorna {valido, monto_solicitado, saldo_disponible, nodo,
        excede, mensaje}.
        """
        monto = self._decimal(monto)
        techo = getattr(bolsa, 'techo', None)
        if techo is None:
            techo = bolsa  # S1: el techo legacy actúa como bolsa

        techo_distribuible = self.get_techo_distribuible(techo)
        distribuido_hojas = self._sum_activo(techo.distribuciones, 'monto_asignado')
        reservado_total = self._sum_activo(techo.distribuciones, 'monto_reserva')

        if exclude_id is not None:
            # Edición de una fila: su monto actual vuelve a la capacidad.
            fila = (
                DistribucionTecho.objects
                .filter(pk=exclude_id, techo=techo, activo=True)
                .first()
            )
            if fila is not None:
                distribuido_hojas -= self._decimal(fila.monto_asignado)
                reservado_total -= self._decimal(fila.monto_reserva)

        saldo_bolsa = self.get_available(bolsa)
        capacidad_techo = techo_distribuible - distribuido_hojas - reservado_total
        saldo_disponible = min(saldo_bolsa, capacidad_techo)

        excede = monto > saldo_disponible
        valido = (not excede) and monto >= 0

        nodo_id = None
        if nodo is not None:
            nodo_id = str(getattr(nodo, 'id', nodo))
        elif unidad is not None:
            nodo_id = str(getattr(unidad, 'id', unidad))
        elif categoria is not None:
            nodo_id = str(getattr(categoria, 'id', categoria))

        if monto < 0:
            mensaje = 'El monto solicitado no puede ser negativo.'
        elif excede:
            mensaje = (
                f'El monto Bs {monto} excede el saldo disponible '
                f'Bs {saldo_disponible}.'
            )
        else:
            mensaje = 'Asignación válida.'

        return {
            'valido': valido,
            'monto_solicitado': monto,
            'saldo_disponible': saldo_disponible,
            'nodo': nodo_id,
            'excede': excede,
            'mensaje': mensaje,
        }


def _estado_operativo_gestion(estado: str) -> str:
    """Mapeo operativo 8→4 de GestionFiscal (Q3).

    Provisional en S1 (gestion_fiscal llega en S2); en S2 se centraliza en
    apps/gestion/services.py como estado_operativo().
    """
    if estado in ('cerrada', 'archivada', 'anulada'):
        return 'CERRADA'
    if estado in ('aprobacion', 'vigente'):
        return 'VIGENTE'
    if estado in ('preparacion', 'abierta', 'formulacion', 'revision', 'consolidacion'):
        return 'BORRADOR'
    return 'BORRADOR'


budget_service = BudgetAllocationService()
