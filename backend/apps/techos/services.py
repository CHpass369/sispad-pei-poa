from decimal import Decimal
import logging

from django.db import transaction
from django.db.models import Sum
from .models import (
    DistribucionTecho,
    GastoObligatorio,
    MovimientoTecho,
    RecursoTecho,
    TechoPresupuestario,
)

logger = logging.getLogger(__name__)


def obtener_saldo_disponible(techo):
    """Wrapper de compatibilidad (D11): delega en BudgetAllocationService.

    Preserva la semántica legacy (saldo por movimientos aprobados, A11) para
    no alterar la salida de los endpoints V1. La ecuación canónica vive en
    BudgetAllocationService.get_available/get_techo_resumen.
    """
    return budget_service.get_saldo_por_movimientos(techo)


def resumen_techo(techo):
    """Wrapper de compatibilidad (D11): resumen unificado del servicio."""
    return budget_service.get_techo_resumen(techo)


def validar_distribucion_no_excede(techo, monto_asignado, exclude_id=None):
    """Wrapper de compatibilidad (D11): delega en validate_allocation con la
    guardia a nivel techo (C3/C6). Resultado: {monto_solicitado,
    saldo_disponible, excede, valido, nodo, mensaje}."""
    return budget_service.validate_allocation(
        techo, monto_asignado, exclude_id=exclude_id,
    )


def validar_movimiento(movimiento):
    """DEPRECADO (C6): wrapper del motor único; no computa saldos propios.

    La validación de saldo reproduce la ecuación legacy por movimientos
    aprobados (get_saldo_por_movimientos, semántica A11 de
    obtener_saldo_disponible) hasta que S3 provea el camino canónico de
    mutación (allocate/reserve/release bajo lock). NO usa can_allocate:
    esa guardia es por distribución (D11) y aflojaría el control de
    dinero de los endpoints V1. Los checks estructurales (montos,
    transferencias) se conservan para no cambiar el contrato (A11).
    """
    logger.warning(
        'validar_movimiento está deprecado; use '
        'BudgetAllocationService.can_allocate/validate_allocation.'
    )
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
            saldo_origen = budget_service.get_saldo_por_movimientos(
                movimiento.source_ceiling,
            )
            if movimiento.amount > saldo_origen:
                errores.append(
                    f'El monto Bs {movimiento.amount} excede el saldo disponible '
                    f'del techo origen Bs {saldo_origen}.'
                )

    return errores


@transaction.atomic
def aplicar_movimiento(movimiento):
    """DEPRECADO (C6): wrapper del motor único; nunca escribe saldos fuera
    del motor.

    La validación reproduce la ecuación legacy por movimientos aprobados
    (get_saldo_por_movimientos, A11) igual que validar_movimiento; no se
    computan saldos aquí ni se usa can_allocate (guardia por distribución,
    D11) para no aflojar el control de dinero de los endpoints V1. La
    escritura del registro MovimientoTecho se conserva para compatibilidad
    V1 (A11); en S3 la escritura pasa por allocate/reserve/release bajo lock.
    """
    logger.warning(
        'aplicar_movimiento está deprecado; la escritura de saldos debe '
        'pasar por BudgetAllocationService (allocate/reserve/release).'
    )
    errores = validar_movimiento(movimiento)
    if errores:
        raise ValueError('; '.join(errores))

    if movimiento.movement_type in ('reduccion', 'reserva', 'liberacion', 'reversion'):
        nuevo_total = budget_service.get_saldo_por_movimientos(
            movimiento.techo, excluir_id=movimiento.pk,
        )
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

    def _sum_hojas_activas(self, techo, campo='monto_asignado') -> Decimal:
        """Σ del campo sobre las filas HOJA activas del techo.

        En la jerarquía bolsa → categoría → UO (S2) la categoría sintética
        agrupa a las hojas y su monto es Σ de las hojas: sumar todo el
        árbol duplicaría el monto (C3 cuenta "Σ activo hojas (bolsas +
        legacy)"). Las filas planas legacy (sin padre, S1) son hojas, por
        lo que el resultado no cambia para el esquema plano.
        """
        return self._sum(
            techo.distribuciones
            .filter(activo=True)
            .exclude(hijos__activo=True),
            campo,
        )

    # ------------------------------------------------------------------
    # Consultas a nivel bolsa (duck-typed: en S1 el techo legacy actúa
    # como bolsa; BolsaPresupuestaria llega en S2)
    # ------------------------------------------------------------------

    def get_amount(self, bolsa) -> Decimal:
        """Monto vigente de la bolsa (monto_vigente, S2). Para el techo
        legacy expone monto_total.

        Fallo ruidoso (no silencioso): una bolsa que no exponga el campo
        esperado indica un renombrado/forma desconocida; devolver 0.00
        permitiría sobre-asignar en silencio (W7).
        """
        if isinstance(bolsa, TechoPresupuestario):
            return self._decimal(bolsa.monto_total)
        try:
            return self._decimal(bolsa.monto_vigente)
        except AttributeError as e:
            raise AttributeError(
                'Bolsa con forma desconocida: '
                f'{type(bolsa).__name__} no expone monto_vigente (¿campo '
                'renombrado en S2?).'
            ) from e

    def get_reserved(self, bolsa) -> Decimal:
        """Monto reservado: columna monto_reservado de la bolsa (S2) o
        Σ monto_reserva de las HOJAS activas del techo legacy.

        Espejo de get_distributed (K2 4R): en la jerarquía sintética
        (MIGRACION LEGACY 0004) la categoría tiene monto_reserva = Σ de sus
        hojas; sumar todas las filas activas duplicaría la reserva (40 vs
        hojas 20) y rompería saldo_disponible contra get_techo_resumen.

        Fallo ruidoso (W7): misma política que get_amount.
        """
        if isinstance(bolsa, TechoPresupuestario):
            return self._sum_hojas_activas(bolsa, 'monto_reserva')
        try:
            return self._decimal(bolsa.monto_reservado)
        except AttributeError as e:
            raise AttributeError(
                'Bolsa con forma desconocida: '
                f'{type(bolsa).__name__} no expone monto_reservado (¿campo '
                'renombrado en S2?).'
            ) from e

    def get_distributed(self, bolsa) -> Decimal:
        """Monto distribuido activo: Σ hojas activas de la bolsa (S2) o
        del techo legacy."""
        if isinstance(bolsa, TechoPresupuestario):
            return self._sum_hojas_activas(bolsa, 'monto_asignado')
        qs = getattr(bolsa, 'distribuciones', None)
        if qs is None:
            qs = bolsa.distribuciontecho_set.all()
        return self._sum(
            qs.filter(activo=True).exclude(hijos__activo=True), 'monto_asignado',
        )

    def get_sum_hijos(self, padre) -> Decimal:
        """Σ monto_asignado de los hijos ACTIVOS del nodo padre (R4.2).

        A diferencia de get_distributed_nodo (saldo de un nodo, que para
        un nodo sin hijos devuelve su monto_asignado), esta operación
        responde SOLO la suma de hijos: un nodo intermedio recién creado
        sin hijos devuelve 0, que es lo que la validación SUM(hijos) ≤
        padre necesita.
        """
        return self._sum_activo(padre.hijos.all(), 'monto_asignado')

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

    def get_available(self, bolsa, exclude_id=None) -> Decimal:
        """Saldo disponible: techo distribuible - distribuido - reservado
        (techo) o vigente - reservado - distribuido (bolsa, S2).

        Con exclude_id se excluye la fila editada (W2): al revalidar una
        hoja, su monto asignado y su reserva vuelven a la capacidad; de lo
        contrario el saldo de la bolsa seguiría contando la fila y el min()
        de validate_allocation rechazaría toda edición positiva.
        """
        distribuido = self.get_distributed(bolsa)
        reservado = self.get_reserved(bolsa)
        if exclude_id is not None:
            techo = (
                bolsa if isinstance(bolsa, TechoPresupuestario)
                else getattr(bolsa, 'techo', None)
            )
            if techo is not None:
                # Solo se excluye si la fila está contada en Σ hojas: una
                # fila con hijos activos (nivel categoría) no está en la
                # suma y su monto no debe volver a la capacidad (W3).
                fila = (
                    DistribucionTecho.objects
                    .filter(pk=exclude_id, techo=techo, activo=True)
                    .exclude(hijos__activo=True)
                    .first()
                )
                if fila is not None:
                    distribuido -= self._decimal(fila.monto_asignado)
                    reservado -= self._decimal(fila.monto_reserva)
        if isinstance(bolsa, TechoPresupuestario):
            return self.get_techo_distribuible(bolsa) - distribuido - reservado
        return self.get_amount(bolsa) - reservado - distribuido

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

        NOTA (W8): este método es por-techo (4 consultas SUM). Para uso
        batch (p. ej. listar techos de una gestión) NO se debe invocar en
        un loop: usar resumen_techos(qs), que agrega con SUMs agrupados en
        una ronda fija de consultas (contrato de salida idéntico).
        """
        gastos = self.get_total_gastos_obligatorios(techo)
        distribuido = self._sum_hojas_activas(techo, 'monto_asignado')
        reservado = self._sum_hojas_activas(techo, 'monto_reserva')
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
            'saldo_disponible': distribuible - distribuido - reservado,
            'excede': distribuido > distribuible,
            'estado': self.estado_techo(techo),
        }

    def resumen_techos(self, techos) -> dict:
        """Resumen batch de N techos (W8) — misma ecuación que
        get_techo_resumen, una sola ronda de SUMs agrupados.

        Reemplaza N invocaciones a get_techo_resumen (4 SUMs por techo) por
        3 SUMs agrupados totales (recursos, gastos activos, hojas activas),
        independientes del número de techos. Contrato de salida IDÉNTICO
        (mismas claves) para no bifurcar la ecuación (D11); el estado
        calculado reutiliza los saldos ya agregados vía estado_techo(saldos).

        Retorna {techo_id_str: resumen}. El serializer V2 lo usa en
        listado y cae a get_techo_resumen solo en detail/fallback.
        """
        techos = list(techos)
        if not techos:
            return {}
        ids = [t.id for t in techos]

        recursos = {
            r['techo_id']: self._decimal(r['total'])
            for r in (
                RecursoTecho.objects.filter(techo_id__in=ids)
                .values('techo_id').annotate(total=Sum('monto'))
            )
        }
        gastos = {
            g['techo_id']: self._decimal(g['total'])
            for g in (
                GastoObligatorio.objects.filter(techo_id__in=ids, activo=True)
                .values('techo_id').annotate(total=Sum('monto'))
            )
        }
        hojas = (
            DistribucionTecho.objects
            .filter(techo_id__in=ids, activo=True)
            .exclude(hijos__activo=True)
            .values('techo_id')
            .annotate(
                asignado=Sum('monto_asignado'),
                reserva=Sum('monto_reserva'),
            )
        )
        distribuido = {h['techo_id']: self._decimal(h['asignado']) for h in hojas}
        reservado = {h['techo_id']: self._decimal(h['reserva']) for h in hojas}

        resumen = {}
        for techo in techos:
            tid = str(techo.id)
            total_recursos = recursos.get(techo.id, Decimal('0.00'))
            total_gastos = gastos.get(techo.id, Decimal('0.00'))
            monto_total = self._decimal(techo.monto_total)
            distribuible = (
                monto_total
                - total_gastos
                - self._decimal(getattr(techo, 'otras_afectaciones', Decimal('0.00')))
            )
            dist = distribuido.get(techo.id, Decimal('0.00'))
            resv = reservado.get(techo.id, Decimal('0.00'))
            saldos = {
                'techo_distribuible': distribuible,
                'monto_distribuido': dist,
                'monto_reservado': resv,
            }
            resumen[tid] = {
                'techo_id': tid,
                'gestion': techo.gestion,
                'monto_total': monto_total,
                'total_recursos': total_recursos,
                'total_gastos_obligatorios': total_gastos,
                'monto_distribuido': dist,
                'monto_reservado': resv,
                'techo_distribuible': distribuible,
                'saldo_disponible': distribuible - dist - resv,
                'excede': dist > distribuible,
                'estado': self.estado_techo(techo, saldos=saldos),
            }
        return resumen

    def estado_techo(self, techo, saldos=None) -> str:
        """Estado calculado del techo (DD3).

        Precedencia: CERRADO > VIGENTE > INCONSISTENTE >
        DISTRIBUCION_COMPLETA > DISTRIBUCION_PARCIAL > EN_CONFIGURACION >
        SIN_CONFIGURAR. En S1 no existe gestion_fiscal ni bolsas: los
        estados CERRADO/VIGENTE/EN_CONFIGURACION quedan inertes hasta S2.

        `saldos` (opcional, W8): dict con techo_distribuible,
        monto_distribuido y monto_reservado ya agregados para uso batch
        (resumen_techos); evita re-agregar en un loop sin bifurcar la
        ecuación (D11).
        """
        gestion = getattr(techo, 'gestion_fiscal', None)
        if gestion is not None:
            operativo = _estado_operativo_gestion(gestion.estado)
            if operativo in ('CERRADA', 'ANULADA'):
                return 'CERRADO'
            if operativo == 'VIGENTE':
                return 'VIGENTE'

        if saldos is None:
            distribuible = self.get_techo_distribuible(techo)
            distribuido = self._sum_hojas_activas(techo, 'monto_asignado')
            reservado = self._sum_hojas_activas(techo, 'monto_reserva')
        else:
            distribuible = saldos['techo_distribuible']
            distribuido = saldos['monto_distribuido']
            reservado = saldos['monto_reservado']
        # C3: Σ activo hojas + reservado_total ≤ techo_distribuible; un
        # sobre-compromiso solo por reservas (monto_asignado 0) también
        # es INCONSISTENTE (fail-loud).
        if distribuido + reservado > distribuible:
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
    # Conciliación de grupos FF/OF (R2.5/Q2) — sin umbral de silencio
    # ------------------------------------------------------------------

    def get_diferencia(self, grupo) -> Decimal:
        """|Σ detalles − monto| del grupo (Decimal exacto, Q2).

        Arimética Decimal sobre NUMERIC(18,2): cualquier |diferencia| > 0
        es CON_DIFERENCIA; nunca se tolera un umbral que oculte errores.
        """
        suma_detalles = self._sum(grupo.detalles.all(), 'monto')
        return abs(suma_detalles - self._decimal(grupo.monto))

    def get_estado_conciliacion(self, grupo) -> str:
        """Estado de conciliación del grupo: PENDIENTE/CONCILIADO/CON_DIFERENCIA."""
        if not grupo.detalles.exists():
            return 'PENDIENTE'
        if self.get_diferencia(grupo) == 0:
            return 'CONCILIADO'
        return 'CON_DIFERENCIA'

    def get_sin_clasificar(self, grupo) -> Decimal:
        """sin_clasificar = monto − corriente − inversión (R4.4)."""
        return (
            self._decimal(grupo.monto)
            - self._decimal(grupo.monto_corriente)
            - self._decimal(grupo.monto_inversion)
        )

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
        """Σ monto_asignado de las hojas activas de distribución de una gestión."""
        return self._sum(
            DistribucionTecho.objects
            .filter(techo__gestion=gestion, activo=True)
            .exclude(hijos__activo=True),
            'monto_asignado',
        )

    def get_saldo_por_distribuir_gestion(self, gestion) -> Decimal:
        """Saldo por distribuir de una gestión: techo agregado - distribuido."""
        return (
            self.get_techo_agregado_gestion(gestion)
            - self.get_distribuido_agregado_gestion(gestion)
        )

    def get_distribuido_por_programa(self, programa) -> Decimal:
        """Σ monto_asignado de las hojas activas de un programa (reportes)."""
        return self._sum(
            DistribucionTecho.objects
            .filter(programa=programa, activo=True)
            .exclude(hijos__activo=True),
            'monto_asignado',
        )

    def get_saldo_por_movimientos(self, techo, excluir_id=None) -> Decimal:
        """Saldo por movimientos aprobados (compatibilidad legacy V1, A11).

        No es la ecuación canónica: reproduce la semántica histórica de
        obtener_saldo_disponible (monto_total ± movimientos aprobados)
        para no alterar la salida de los endpoints V1. La ecuación
        canónica vive en get_available/get_techo_resumen.

        excluir_id excluye un movimiento concreto (re-validación de un
        movimiento ya persistido, como hacía aplicar_movimiento legacy).
        """
        movimientos = MovimientoTecho.objects.filter(
            techo=techo, approved_by__isnull=False,
        )
        if excluir_id is not None:
            movimientos = movimientos.exclude(pk=excluir_id)
        saldo = self._decimal(techo.monto_total)
        for mov in movimientos:
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
        nodo=None, exclude_id=None, monto_reserva_nuevo=0,
    ) -> dict:
        """Valida una asignación contra la capacidad efectiva (R5.4).

        Capacidad efectiva = min(saldo de la bolsa, techo_distribuible
        - Σ activo hojas - reservado_total) — guardia a nivel techo (C3):
        las bolsas se crean desde Σ recursos y su Σ puede exceder
        techo_distribuible, por lo que la bolsa individual no alcanza a
        ver el exceso. No muta ni adquiere locks (S3).

        monto_reserva_nuevo (C3/D2): la fila que se está escribiendo
        compromete monto_asignado + monto_reserva; el monto_reserva en
        memoria se resta de la capacidad igual que el monto_asignado
        (validate_allocation solo recibe el monto_asignado como `monto`,
        y el caller DistribucionTecho.clean() pasa su monto_reserva aquí;
        con exclude_id el monto viejo de la fila ya volvió a la
        capacidad).

        Retorna {valido, monto_solicitado, saldo_disponible, nodo,
        excede, mensaje}.
        """
        monto = self._decimal(monto)
        monto_reserva_nuevo = self._decimal(monto_reserva_nuevo)
        techo = getattr(bolsa, 'techo', None)
        if techo is None:
            techo = bolsa  # S1: el techo legacy actúa como bolsa

        techo_distribuible = self.get_techo_distribuible(techo)
        distribuido_hojas = self._sum_hojas_activas(techo, 'monto_asignado')
        reservado_total = self._sum_hojas_activas(techo, 'monto_reserva')

        if exclude_id is not None:
            # Edición de una hoja: su monto actual vuelve a la capacidad.
            # (una fila con hijos activos no está en Σ hojas y no se resta)
            fila = (
                DistribucionTecho.objects
                .filter(pk=exclude_id, techo=techo, activo=True)
                .exclude(hijos__activo=True)
                .first()
            )
            if fila is not None:
                distribuido_hojas -= self._decimal(fila.monto_asignado)
                reservado_total -= self._decimal(fila.monto_reserva)

        # W2: el saldo de la bolsa también excluye la fila editada; si no,
        # min(saldo_bolsa, capacidad_techo) colapsa al saldo viejo y toda
        # edición positiva se rechaza (doble conteo).
        saldo_bolsa = self.get_available(bolsa, exclude_id=exclude_id)
        capacidad_techo = (
            techo_distribuible - distribuido_hojas - reservado_total
            - monto_reserva_nuevo
        )
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
    """Mapeo operativo 10→4 de GestionFiscal (Q3).

    Centralizado en apps/gestion/services.py (estado_operativo); este
    wrapper evita importar gestion en el módulo raíz (evita dependencias
    circulares) y mantiene un único punto de llamada.
    """
    from apps.gestion.services import estado_operativo
    return estado_operativo(estado)


budget_service = BudgetAllocationService()
