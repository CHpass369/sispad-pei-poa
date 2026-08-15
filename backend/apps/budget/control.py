"""Núcleo financiero transaccional del ciclo presupuestario SIS-POA (Fase 8).

`BudgetControlService` centraliza TODAS las reglas monetarias del ciclo
(§85-88 y §109 del prompt maestro):

    - Lectura de saldos por fuente (techo, distribuido, reservado, disponible)
      calculados desde la versión FIJADA del techo directivo.
    - Escritura transaccional con `select_for_update` sobre las filas de
      `CeilingResource` de la versión fijada: el lock serializa los consumos
      concurrentes sobre la misma fuente y garantiza que NUNCA se consuma más
      que el saldo (§87 — Usuario A 80.000 + Usuario B 50.000 sobre 100.000 →
      el segundo falla con BUDGET_EXCEEDED).
    - `reserve`/`release` (refactor transaccional de `crear_reserva`/
      `liberar_reserva` de services.py) y `apply_movement` preparado para
      reformulaciones (Fase 10).

Las funciones históricas de `services.py` (crear_allocation, crear_reserva,
liberar_reserva, _bloquear_fuentes, …) delegan en este servicio sin cambiar
sus firmas ni su comportamiento; el control central vive ACÁ (Fase 8).

Convenciones:
    - Montos Decimal (NUMERIC(18,2)), nunca float.
    - Servicio SIN ESTADO: todos los métodos son de clase; la clase es un
      namespace del kernel financiero y el estado vive en la BD.
    - Los métodos `get_*` son lecturas (no lockean); los métodos de
      escritura (`reserve`, `release`, `apply_movement`) corren en
      `transaction.atomic` y lockean las filas del techo fijado.

Fases futuras (NO ampliar alcance acá):
    - Fase 11: auditoría transversal completa (la reformulación ya registra
      EventoAuditoria en aplicar; la UI de consulta es Fase 11).

Fase 9 (objetos del gasto): `get_allocated_to_expense_objects`/
`get_allocation_available`/`validate_expense_object` ya están completos
sobre `ExpenseObjectAllocation`; la programación la ejecuta
`services.programar_objeto_gasto` (upsert, BUDGET_EXCEEDED → HTTP 409).

Fase 10 (reformulaciones): `apply_movement` implementa el movimiento
atómico TRASPASO (origen → destino por fuente) con locks y saldos
antes/después; `services.aplicar_reform` lo reutiliza y resuelve
INCREMENTO/DISMINUCION/CAMBIO_FUENTE sobre el mismo kernel.
"""
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models, transaction

from apps.auditoria.models import EventoAuditoria
from apps.auditoria.services import registrar_evento

from .models import (
    Allocation,
    AllocationSource,
    EstadoApertura,
    EstadoReserva,
    EstadosTecho,
    ExpenseObjectAllocation,
    Reserve,
    TipoReserva,
)
from .services import (
    ErrorDisponibilidad,
    ErrorObjetoGastoExcedido,
    _disponible_por_fuente,
    _version_techo_fijada,
    distribuido_por_fuente,
    reservado_por_fuente,
    techo_distribuible_por_fuente,
    validar_distribucion_completa,
    validar_gestion_para_distribucion,
    version_distribucion_activa,
)


class BudgetControlService:
    """Núcleo financiero del SIS-POA: saldos y escrituras transaccionales.

    Sin estado: todos los métodos son estáticos y reciben sus dependencias
    explícitamente (la gestión, la apertura o la reserva). El patrón de
    bloqueo (`select_for_update` sobre las filas de recurso de la versión
    FIJADA del techo) vive acá y lo reutilizan `services.py`, `territorial.py`
    y las fases 9-10.
    """

    # ------------------------------------------------------------------
    # Lectura: saldos por fuente (desde la versión FIJADA del techo)
    # ------------------------------------------------------------------

    @staticmethod
    def get_directive_ceiling(gestion):
        """Techo bruto y por fuente de la versión FIJADA; {} si no hay.

        `por_fuente` es {fuente_id: monto bruto} y `techo_bruto` la suma de
        TODOS los recursos de la versión fijada (incluye los sin fuente).
        Sin techo fijado devuelve {} (operaciones bloqueadas).
        """
        version = _version_techo_fijada(gestion)
        if version is None:
            return {}
        por_fuente = {}
        total = Decimal('0.00')
        for recurso in version.recursos.all():
            total += recurso.monto
            if recurso.fuente_id:
                por_fuente[recurso.fuente_id] = (
                    por_fuente.get(recurso.fuente_id, Decimal('0.00'))
                    + recurso.monto
                )
        return {
            'gestion': gestion.anio,
            'version': version.numero,
            'techo_bruto': total,
            'por_fuente': por_fuente,
        }

    @staticmethod
    def get_distributable_ceiling(gestion):
        """Techo distribuible por fuente: {fuente_id: bruto − obligatorios}.

        Solo fuentes con recursos; sin techo fijado devuelve {}.
        """
        return techo_distribuible_por_fuente(gestion)

    @staticmethod
    def get_distributed(gestion):
        """{fuente_id: monto} distribuido por aperturas (no CERRADAS)."""
        return distribuido_por_fuente(gestion)

    @staticmethod
    def get_reserved(gestion):
        """{fuente_id: monto} reservado (reservas ACTIVAS)."""
        return reservado_por_fuente(gestion)

    @staticmethod
    def get_available_for_distribution(gestion):
        """{fuente_id: monto} disponible = techo − distribuido − reservado.

        Sin techo fijado devuelve {} (distribución bloqueada).
        """
        return _disponible_por_fuente(gestion)

    # ------------------------------------------------------------------
    # Lectura: aperturas (programación por objeto del gasto = Fase 9)
    # ------------------------------------------------------------------

    @staticmethod
    def get_allocation_ceiling(allocation):
        """Total de fuentes de la apertura (techo de la apertura)."""
        total = allocation.fuentes.aggregate(total=models.Sum('monto'))['total']
        return total if total is not None else Decimal('0.00')

    @staticmethod
    def get_allocated_to_expense_objects(allocation):
        """Programado en objetos del gasto de la apertura (§90, Fase 9).

        Σ montos de `ExpenseObjectAllocation` de la apertura; Decimal con
        0.00 de default si no hay programación.
        """
        total = (
            ExpenseObjectAllocation.objects
            .filter(allocation=allocation)
            .aggregate(total=models.Sum('monto'))['total']
        )
        return total if total is not None else Decimal('0.00')

    @staticmethod
    def get_allocation_available(allocation):
        """Disponible de la apertura = techo − programado (§90-91)."""
        return (
            BudgetControlService.get_allocation_ceiling(allocation)
            - BudgetControlService.get_allocated_to_expense_objects(allocation)
        )

    # ------------------------------------------------------------------
    # Validaciones
    # ------------------------------------------------------------------

    @staticmethod
    def validate_distribution(gestion):
        """Valida la completitud de la distribución (§49-52): Σfuente =
        techo − reservas. Devuelve {valida, diferencias}."""
        return validar_distribucion_completa(gestion)

    @staticmethod
    def validate_expense_object(allocation, objeto_gasto_id, monto):
        """Valida una programación por objeto del gasto (§90-91, Fase 9).

        Convención del repo: LANZA ValidationError cuando no pasa (la API
        mapea la excepción a `{valido: False, errores}` en POST
        /control/validate/ o a HTTP 409) y devuelve {'valido': True} cuando
        sí. Valida: apertura existente y ACTIVA; y si viene objeto del gasto
        + monto (la rama `allocation` del endpoint solo pregunta por la
        apertura), versión de distribución FIJADA, objeto del gasto
        existente y monto <= disponible de la apertura (BUDGET_EXCEEDED con
        details {requested, available, difference}).
        """
        if not isinstance(allocation, Allocation):
            allocation = Allocation.objects.filter(pk=allocation).first()
        if allocation is None:
            raise ValidationError('La apertura no existe.')
        if allocation.estado != EstadoApertura.ACTIVA:
            raise ValidationError(
                f'La apertura está {allocation.get_estado_display()}; '
                'debe estar ACTIVA para programar.'
            )
        if objeto_gasto_id is None and monto is None:
            return {'valido': True}
        version = allocation.version
        if version is None or not version.inmutable or \
                version.estado != EstadosTecho.FIJADO:
            raise ValidationError(
                'La distribución debe estar fijada para programar objetos '
                'del gasto.'
            )
        from apps.catalogos.models import ObjetoGasto
        objeto = ObjetoGasto.objects.filter(
            pk=getattr(objeto_gasto_id, 'id', objeto_gasto_id),
        ).first()
        if objeto is None:
            raise ValidationError('El objeto del gasto no existe.')
        monto_dec = (
            monto if isinstance(monto, Decimal) else Decimal(str(monto))
        )
        disponible = BudgetControlService.get_allocation_available(allocation)
        if monto_dec > disponible:
            raise ErrorObjetoGastoExcedido(monto_dec, disponible)
        return {'valido': True}

    # ------------------------------------------------------------------
    # Escritura: lock + saldos (reglas §87, nunca más que el saldo)
    # ------------------------------------------------------------------

    @staticmethod
    def _bloquear_fuentes(gestion, fuente_ids):
        """select_for_update sobre las filas de recurso de las fuentes.

        Las filas del techo FIJADO son inmutables; el lock serializa las
        validaciones de disponibilidad concurrentes sobre la misma fuente
        (el segundo request re-lee los agregados ya commiteados y falla con
        BUDGET_EXCEEDED en lugar de exceder el saldo).
        """
        if not fuente_ids:
            return
        version = _version_techo_fijada(gestion)
        if version is None:
            return
        filas = (
            version.recursos
            .filter(fuente_id__in=fuente_ids)
            .order_by('fuente_id', 'id')
            .select_for_update()
        )
        list(filas)

    @staticmethod
    @transaction.atomic
    def reserve(gestion, fuente, organismo, monto, motivo, usuario, tipo=None):
        """Crea una reserva ACTIVA sobre una fuente con lock (Fase 8).

        Refactor transaccional de `crear_reserva` (services.py): valida la
        gestión, la versión activa de distribución, bloquea las filas del
        techo fijado de la fuente y solo crea la reserva si no excede el
        disponible (BUDGET_EXCEEDED con requested/available/difference si
        no). Registra auditoría.
        """
        validar_gestion_para_distribucion(gestion)
        techo = techo_distribuible_por_fuente(gestion)
        if not techo:
            raise ValidationError(
                f'La gestión {gestion.anio} no tiene un techo directivo '
                'fijado; la distribución está bloqueada.'
            )
        version = version_distribucion_activa(gestion)
        if version.inmutable:
            raise ValidationError(
                'La versión de distribución está fijada (inmutable); '
                'no se pueden crear reservas.'
            )

        fuente_id = getattr(fuente, 'id', fuente)
        if not fuente_id:
            raise ValidationError('Debe indicar la fuente de financiamiento.')
        if monto is None or monto <= 0:
            raise ValidationError('El monto de la reserva debe ser mayor que 0.')
        organismo_id = getattr(organismo, 'id', organismo) if organismo else None

        BudgetControlService._bloquear_fuentes(gestion, {fuente_id})
        disponible = _disponible_por_fuente(gestion)
        saldo = disponible.get(fuente_id, Decimal('0.00'))
        if monto > saldo:
            raise ErrorDisponibilidad(fuente_id, monto, saldo)

        reserva = Reserve.objects.create(
            gestion=gestion,
            version=version,
            fuente_id=fuente_id,
            organismo_id=organismo_id,
            tipo=tipo or TipoReserva.OTRA,
            motivo=motivo or '',
            monto=monto,
            estado=EstadoReserva.ACTIVA,
            created_by=usuario,
            updated_by=usuario,
        )
        registrar_evento(
            usuario,
            EventoAuditoria.Accion.CREAR,
            'Reserve',
            reserva.id,
            resumen=(
                f'Reserva {reserva.get_tipo_display()} de {monto} creada '
                f'(gestión {gestion.anio})'
            ),
            datos_posteriores={'monto': str(monto), 'tipo': reserva.tipo},
            gestion=gestion.anio,
        )
        return reserva

    @staticmethod
    @transaction.atomic
    def release(reserva, usuario):
        """Libera una reserva ACTIVA (LIBERADA); devuelve el disponible.

        Refactor transaccional de `liberar_reserva` (services.py). La
        liberación no consume saldo, pero lockea la fuente para serializarse
        contra reservas concurrentes de la misma fuente.
        """
        if reserva.estado == EstadoReserva.LIBERADA:
            raise ValidationError('La reserva ya está liberada.')
        if reserva.version is not None and reserva.version.inmutable:
            raise ValidationError(
                'La reserva pertenece a una versión de distribución fijada '
                '(inmutable); no se puede liberar.'
            )
        BudgetControlService._bloquear_fuentes(
            reserva.gestion,
            {reserva.fuente_id} if reserva.fuente_id else set(),
        )
        reserva.estado = EstadoReserva.LIBERADA
        reserva.updated_by = usuario
        reserva.save(update_fields=['estado', 'updated_by', 'updated_at'])
        registrar_evento(
            usuario,
            EventoAuditoria.Accion.MODIFICAR,
            'Reserve',
            reserva.id,
            resumen=(
                f'Reserva de {reserva.monto} liberada '
                f'(gestión {reserva.gestion.anio})'
            ),
            datos_previos={'estado': EstadoReserva.ACTIVA},
            datos_posteriores={'estado': EstadoReserva.LIBERADA},
            gestion=reserva.gestion.anio,
        )
        return reserva

    @staticmethod
    @transaction.atomic
    def apply_movement(orig, dest, fuente, organismo, monto, motivo, usuario):
        """Mueve `monto` de una apertura a otra POR FUENTE (Fase 10).

        Movimiento básico de reformulación TRASPASO (origen → destino):
        reduce el `AllocationSource` (origen, fuente, organismo) y aumenta
        el de (destino, fuente, organismo), creándolo si no existe.

        Concurrencia (§87): locks sobre la fila de la apertura origen
        (`select_for_update`) y sobre las filas del techo fijado de la
        fuente (`_bloquear_fuentes`), que es el punto de serialización de
        TODAS las escrituras del ciclo.

        Validaciones (reglas §151 en backend, innegociables):
            - monto > 0 y aperturas existentes.
            - saldo_origen >= monto → si no, `ErrorDisponibilidad`
              (code BUDGET_EXCEEDED, details requested/available/difference).
            - el saldo resultante del DESTINO no excede el techo distribuible
              de la fuente (`techo_distribuible_por_fuente`); en un traspaso
              el agregado de la fuente se conserva, así que solo dispara si
              la distribución ya estaba inconsistente (red de seguridad).

        Devuelve {'valido', 'movido', 'origen', 'destino', 'fuente',
        'saldo_antes', 'saldo_despues'} — los saldos del AllocationSource de
        ORIGEN antes/después, que `services.aplicar_reform` persiste en el
        `ReformMovement` (histórico).
        """
        if monto is None or monto <= 0:
            raise ValidationError('El monto del movimiento debe ser mayor que 0.')
        if fuente is None:
            raise ValidationError(
                'El movimiento entre aperturas debe indicar una fuente '
                'de financiamiento.'
            )
        origen = (
            Allocation.objects
            .select_for_update()
            .filter(pk=orig.pk)
            .first()
        )
        if origen is None:
            raise ValidationError('La apertura de origen no existe.')
        destino = (
            Allocation.objects
            .select_for_update()
            .filter(pk=dest.pk)
            .first()
        )
        if destino is None:
            raise ValidationError('La apertura de destino no existe.')

        fuente_id = getattr(fuente, 'id', fuente)
        organismo_id = getattr(organismo, 'id', organismo) if organismo else None
        BudgetControlService._bloquear_fuentes(
            origen.gestion, {fuente_id},
        )

        # Lock y lectura del saldo del origen (Fase 8: validaba sin mover;
        # Fase 10: el movimiento es atómico con saldos antes/después).
        origen_src = (
            AllocationSource.objects
            .select_for_update()
            .filter(
                allocation=origen, fuente_id=fuente_id,
                organismo_id=organismo_id,
            )
            .first()
        )
        saldo_antes = (
            origen_src.monto if origen_src is not None else Decimal('0.00')
        )
        if monto > saldo_antes:
            raise ErrorDisponibilidad(fuente_id, monto, saldo_antes)

        # Destino: no excede el techo distribuible de la fuente (§96).
        destino_src = (
            AllocationSource.objects
            .select_for_update()
            .filter(
                allocation=destino, fuente_id=fuente_id,
                organismo_id=organismo_id,
            )
            .first()
        )
        saldo_destino = (
            destino_src.monto if destino_src is not None else Decimal('0.00')
        )
        techo = techo_distribuible_por_fuente(origen.gestion)
        if saldo_destino + monto > techo.get(fuente_id, Decimal('0.00')):
            raise ValidationError(
                'El saldo resultante del destino supera el techo '
                'distribuible de la fuente.'
            )

        # Aplicación atómica del movimiento.
        origen_src.monto = saldo_antes - monto
        origen_src.updated_by = usuario
        origen_src.save(update_fields=['monto', 'updated_by', 'updated_at'])
        if destino_src is None:
            destino_src = AllocationSource.objects.create(
                allocation=destino, fuente_id=fuente_id,
                organismo_id=organismo_id, monto=monto,
                created_by=usuario, updated_by=usuario,
            )
        else:
            destino_src.monto = saldo_destino + monto
            destino_src.updated_by = usuario
            destino_src.save(update_fields=['monto', 'updated_by', 'updated_at'])

        return {
            'valido': True,
            'movido': True,
            'origen': str(origen.id),
            'destino': str(destino.id),
            'fuente': str(fuente_id),
            'saldo_antes': saldo_antes,
            'saldo_despues': origen_src.monto,
        }

    # ------------------------------------------------------------------
    # Resumen consolidado (endpoint GET /budget/control/summary/)
    # ------------------------------------------------------------------

    @staticmethod
    def get_summary(gestion):
        """Resumen consolidado del control presupuestario por fuente.

        {gestion, techo_bruto, techo_distribuible, distribuido, reservado,
        disponible, porcentaje, por_fuente:[{fuente, denominacion, techo,
        distribuido, reservado, disponible}]}.

        Invariante por fuente (exacta, sin redondeos):
            techo = distribuido + reservado + disponible.
        `techo_distribuible` es la suma de los techos por fuente (bruto −
        obligatorios); `techo_bruto` suma todos los recursos de la versión
        fijada. Sin techo fijado devuelve ceros con por_fuente [].
        """
        from apps.catalogos.models import FuenteFinanciamiento

        ceiling = BudgetControlService.get_directive_ceiling(gestion)
        techo = BudgetControlService.get_distributable_ceiling(gestion)
        distribuido = BudgetControlService.get_distributed(gestion)
        reservado = BudgetControlService.get_reserved(gestion)

        if not ceiling:
            return {
                'gestion': gestion.anio,
                'techo_bruto': Decimal('0.00'),
                'techo_distribuible': Decimal('0.00'),
                'distribuido': Decimal('0.00'),
                'reservado': Decimal('0.00'),
                'disponible': Decimal('0.00'),
                'porcentaje': 0.0,
                'por_fuente': [],
            }

        fuente_ids = set(techo) | set(distribuido) | set(reservado)
        fuentes = (
            {f.id: f for f in FuenteFinanciamiento.objects.filter(id__in=fuente_ids)}
            if fuente_ids else {}
        )

        por_fuente = []
        total_techo = Decimal('0.00')
        total_distribuido = Decimal('0.00')
        total_reservado = Decimal('0.00')
        total_disponible = Decimal('0.00')
        for fid in sorted(
            fuente_ids,
            key=lambda x: (fuentes[x].codigo if x in fuentes else ''),
        ):
            t = techo.get(fid, Decimal('0.00'))
            d = distribuido.get(fid, Decimal('0.00'))
            r = reservado.get(fid, Decimal('0.00'))
            disp = t - d - r
            total_techo += t
            total_distribuido += d
            total_reservado += r
            total_disponible += disp
            por_fuente.append({
                'fuente': str(fid),
                'denominacion': fuentes[fid].denominacion if fid in fuentes else '-',
                'techo': t,
                'distribuido': d,
                'reservado': r,
                'disponible': disp,
            })

        porcentaje = (
            round(float(total_distribuido / total_techo * 100), 2)
            if total_techo else 0.0
        )
        return {
            'gestion': gestion.anio,
            'techo_bruto': ceiling['techo_bruto'],
            'techo_distribuible': total_techo,
            'distribuido': total_distribuido,
            'reservado': total_reservado,
            'disponible': total_disponible,
            'porcentaje': porcentaje,
            'por_fuente': por_fuente,
        }
