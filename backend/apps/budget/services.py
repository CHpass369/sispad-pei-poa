"""Servicios del ciclo presupuestario SIS-POA.

Fase 1 (gestión fiscal): bloqueos por gestión (§10 del prompt maestro) — las
fases 2+ validan el estado de la gestión a través de estas funciones antes de
operar (techo directivo, distribución, fijación, reformulaciones…).

Fase 2 (techo directivo): composición, ciclo de estados de la versión
(BORRADOR → EN_REVISION → APROBADO → FIJADO, con OBSERVADO), fijación inmutable
con checksum SHA-256 (§24-25) y ajustes por versión nueva (§25).

Fase 8 (control presupuestario): el CONTROL CENTRAL vive en `control.py`
(`BudgetControlService`): reglas monetarias transaccionales con
`select_for_update` sobre las filas del techo fijado, saldos por fuente y
`reserve`/`release`/`apply_movement`. Las funciones históricas de este módulo
(`crear_allocation`, `crear_reserva`, `liberar_reserva`, `_bloquear_fuentes`)
delegan en él sin cambiar firmas ni comportamiento.

Estados del ciclo usados (nuevos códigos de `GestionFiscal.Estado`):
    CONFIGURACION → HABILITADA → EN_FORMULACION → VIGENTE → CERRADA
Los estados legacy se reconocen en los helpers para no romper la UI V1
(mapeo: preparacion≈CONFIGURACION, abierta≈HABILITADA,
formulacion≈EN_FORMULACION, cerrada≈CERRADA).
"""
import hashlib
import json
from decimal import ROUND_HALF_UP, Decimal

from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.utils import timezone

from apps.auditoria.models import EventoAuditoria
from apps.auditoria.services import registrar_evento
from apps.gestion.models import CicloFormulacion, EtapaFormulacion, GestionFiscal

from .models import (
    Allocation,
    AllocationSource,
    CeilingResource,
    DirectiveCeiling,
    DirectiveCeilingVersion,
    DistributionVersion,
    EstadoApertura,
    EstadoReserva,
    EstadosReform,
    EstadosTecho,
    ExpenseObjectAllocation,
    MandatoryExpense,
    Reform,
    ReformMovement,
    Reserve,
    TipoMovimientoReform,
    TipoReform,
    TipoReserva,
)

# Estados del ciclo presupuestario (nuevos códigos).
ESTADO_CONFIGURACION = 'CONFIGURACION'
ESTADO_HABILITADA = 'HABILITADA'
ESTADO_EN_FORMULACION = 'EN_FORMULACION'
ESTADO_VIGENTE = 'VIGENTE'
ESTADO_CERRADA = 'CERRADA'

# Estados desde los que la gestión ya no se puede habilitar.
ESTADOS_NO_HABILITABLES = {
    ESTADO_VIGENTE,
    ESTADO_CERRADA,
    GestionFiscal.Estado.CERRADA,
    GestionFiscal.Estado.ARCHIVADA,
}


def gestion_habilitada(gestion):
    """¿La gestión está habilitada para el ciclo presupuestario? (§10)"""
    return gestion.estado in (ESTADO_HABILITADA, GestionFiscal.Estado.ABIERTA)


def gestion_en_formulacion(gestion):
    """¿La gestión está en fase de formulación? (§10)"""
    return gestion.estado in (
        ESTADO_EN_FORMULACION,
        GestionFiscal.Estado.FORMULACION,
    )


def validar_gestion_para_techo(gestion):
    """Valida que la gestión esté habilitada para fijar techo directivo.

    Lanza ValidationError en caso contrario; las fases 2+ la usan antes de
    crear/editar techos.
    """
    if not gestion_habilitada(gestion):
        raise ValidationError(
            f'La gestión {gestion.anio} no está habilitada para fijar techo '
            f'directivo (estado actual: {gestion.get_estado_display()}).'
        )
    return True


@transaction.atomic
def habilitar_gestion(gestion, usuario):
    """Habilita la gestión para el ciclo presupuestario (HABILITADA).

    Registra EventoAuditoria (accion=modificar; no existe accion habilitar
    en el catálogo de `auditoria.EventoAuditoria.Accion`).
    """
    if gestion_habilitada(gestion):
        raise ValidationError(f'La gestión {gestion.anio} ya está habilitada.')
    if gestion.estado in ESTADOS_NO_HABILITABLES:
        raise ValidationError(
            f'La gestión {gestion.anio} está {gestion.get_estado_display()}; '
            f'no se puede habilitar.'
        )

    estado_previo = gestion.estado
    gestion.estado = ESTADO_HABILITADA
    gestion.fecha_apertura = timezone.now()
    gestion.save(update_fields=['estado', 'fecha_apertura', 'actualizado_en'])
    registrar_evento(
        usuario,
        EventoAuditoria.Accion.MODIFICAR,
        'GestionFiscal',
        gestion.id,
        resumen=f'Gestión {gestion.anio} habilitada para el ciclo presupuestario',
        datos_previos={'estado': estado_previo},
        datos_posteriores={
            'estado': gestion.estado,
            'fecha_apertura': gestion.fecha_apertura.isoformat(),
        },
        gestion=gestion.anio,
    )
    return gestion


@transaction.atomic
def cerrar_gestion(gestion, usuario):
    """Cierra la gestión del ciclo presupuestario (CERRADA) y registra auditoría."""
    if gestion.estado in (ESTADO_CERRADA, GestionFiscal.Estado.CERRADA):
        raise ValidationError(f'La gestión {gestion.anio} ya está cerrada.')
    if gestion.estado == GestionFiscal.Estado.ARCHIVADA:
        raise ValidationError(
            f'La gestión {gestion.anio} está archivada; no se puede cerrar.'
        )

    estado_previo = gestion.estado
    gestion.estado = ESTADO_CERRADA
    gestion.fecha_cierre = timezone.now()
    gestion.save(update_fields=['estado', 'fecha_cierre', 'actualizado_en'])
    registrar_evento(
        usuario,
        EventoAuditoria.Accion.CERRAR,
        'GestionFiscal',
        gestion.id,
        resumen=f'Gestión {gestion.anio} cerrada (ciclo presupuestario)',
        datos_previos={'estado': estado_previo},
        datos_posteriores={
            'estado': gestion.estado,
            'fecha_cierre': gestion.fecha_cierre.isoformat(),
        },
        gestion=gestion.anio,
    )
    return gestion


@transaction.atomic
def heredar_configuracion(gestion_nueva, gestion_origen):
    """Copia la configuración de ciclos/etapas de formulación de la gestión
    origen a la nueva (solo configuración; sin datos de formulación)."""
    for ciclo in gestion_origen.ciclos_formulacion.all():
        nuevo_ciclo = CicloFormulacion.objects.create(
            gestion=gestion_nueva,
            nombre=ciclo.nombre,
            descripcion=ciclo.descripcion,
            fecha_inicio=ciclo.fecha_inicio,
            fecha_cierre=ciclo.fecha_cierre,
            fecha_cierre_prorroga=ciclo.fecha_cierre_prorroga,
            activo=ciclo.activo,
            orden=ciclo.orden,
        )
        for etapa in ciclo.etapas.all():
            EtapaFormulacion.objects.create(
                ciclo=nuevo_ciclo,
                codigo=etapa.codigo,
                nombre=etapa.nombre,
                descripcion=etapa.descripcion,
                fecha_inicio=etapa.fecha_inicio,
                fecha_cierre=etapa.fecha_cierre,
                completada=False,
                orden=etapa.orden,
            )
    return gestion_nueva


# ===========================================================================
# Fase 2 — Techo Directivo
# ===========================================================================

# Acciones del catálogo `auditoria.EventoAuditoria.Accion` usadas por el ciclo:
#   enviar_a_revision → ENVIAR · observar → DEVOLVER · aprobar → APROBAR ·
#   fijar_techo → APROBAR (no existe acción "fijar"; la más cercana es aprobar,
#   se distingue por el resumen) · ajuste_de_techo → CREAR.


def _suma_montos(qs):
    """Suma de montos de un queryset de recursos/gastos (Decimal, sin float)."""
    total = qs.aggregate(total=models.Sum('monto'))['total']
    return total if total is not None else Decimal('0.00')


def obtener_version_actual(ceiling):
    """Versión vigente del techo (`version_actual`); None si no existe."""
    if ceiling.version_actual is None:
        return None
    return (
        DirectiveCeilingVersion.objects
        .filter(ceiling=ceiling, numero=ceiling.version_actual)
        .first()
    )


def composicion_techo(ceiling):
    """Composición del techo directivo (§22).

    Retorna los montos como Decimal (el borde API los serializa a str,
    convención COERCE_DECIMAL_TO_STRING de DRF):
        sigep / municipales / saldos / otros   → recursos por origen
        gastos_obligatorios                    → total a descontar
        reservas                               → 0 en esta fase
        techo_bruto        = SIGEP+MUNICIPAL+SALDO+OTRO
        techo_distribuible = bruto − obligatorios
        por_fuente         → agregación por fuente de financiamiento
                             (sin fuente → 'SIN_FUENTE')

    La deducción de gastos obligatorios por FF/OF individual se aplica en la
    Fase 4 (distribución); acá se resta del total general (regla §22: si el
    gasto obligatorio no tiene fuente, se resta del total general).
    """
    version = obtener_version_actual(ceiling)
    recursos = version.recursos if version else CeilingResource.objects.none()
    gastos = (
        version.gastos_obligatorios
        if version else MandatoryExpense.objects.none()
    )

    sigep = _suma_montos(recursos.filter(origen='SIGEP'))
    municipales = _suma_montos(recursos.filter(origen='MUNICIPAL'))
    saldos = _suma_montos(recursos.filter(origen='SALDO'))
    otros = _suma_montos(recursos.filter(origen='OTRO'))
    gastos_obligatorios = _suma_montos(gastos)
    techo_bruto = sigep + municipales + saldos + otros
    techo_distribuible = techo_bruto - gastos_obligatorios

    por_fuente = []
    if version:
        agrupados = (
            recursos.values('fuente__codigo', 'fuente__denominacion')
            .annotate(monto=models.Sum('monto'))
            .order_by('fuente__codigo')
        )
        for fila in agrupados:
            codigo = fila['fuente__codigo'] or 'SIN_FUENTE'
            denominacion = fila['fuente__denominacion'] or 'Sin fuente'
            por_fuente.append({
                'fuente': codigo,
                'denominacion': denominacion,
                'monto': fila['monto'] or Decimal('0.00'),
            })

    return {
        'gestion': ceiling.gestion.anio,
        'version': version.numero if version else None,
        'estado': version.estado if version else None,
        'sigep': sigep,
        'municipales': municipales,
        'saldos': saldos,
        'otros': otros,
        'gastos_obligatorios': gastos_obligatorios,
        'reservas': Decimal('0.00'),
        'techo_bruto': techo_bruto,
        'techo_distribuible': techo_distribuible,
        'por_fuente': por_fuente,
    }


@transaction.atomic
def crear_version_inicial(ceiling, usuario):
    """Crea la versión 1 (BORRADOR) del techo directivo."""
    if DirectiveCeilingVersion.objects.filter(
        ceiling=ceiling, numero=1
    ).exists():
        raise ValidationError(
            f'El techo de la gestión {ceiling.gestion.anio} ya tiene la '
            'versión 1.'
        )
    version = DirectiveCeilingVersion.objects.create(
        ceiling=ceiling,
        numero=1,
        estado=EstadosTecho.BORRADOR,
        created_by=usuario,
        updated_by=usuario,
    )
    registrar_evento(
        usuario,
        EventoAuditoria.Accion.CREAR,
        'DirectiveCeilingVersion',
        version.id,
        version=version.numero,
        resumen=(
            f'Techo directivo v1 creado para la gestión '
            f'{ceiling.gestion.anio}'
        ),
        gestion=ceiling.gestion.anio,
    )
    return version


def _transicionar(version, destino, usuario, accion, resumen):
    """Aplica una transición de estado válida y registra auditoría."""
    if version.estado == destino:
        raise ValidationError(
            f'La versión ya está en estado {version.get_estado_display()}.'
        )
    if destino not in EstadosTecho.TRANSICIONES.get(version.estado, set()):
        raise ValidationError(
            f'No se puede pasar la versión de '
            f'{version.get_estado_display()} a {dict(EstadosTecho.CHOICES)[destino]}.'
        )
    estado_previo = version.estado
    version.estado = destino
    version.save(update_fields=['estado', 'updated_at'])
    ceiling = version.ceiling
    ceiling.estado = destino
    ceiling.save(update_fields=['estado', 'updated_at'])
    registrar_evento(
        usuario,
        accion,
        'DirectiveCeilingVersion',
        version.id,
        version=version.numero,
        resumen=resumen,
        datos_previos={'estado': estado_previo},
        datos_posteriores={'estado': version.estado},
        gestion=ceiling.gestion.anio,
    )
    return version


def enviar_a_revision(version, usuario):
    """BORRADOR|OBSERVADO → EN_REVISION."""
    return _transicionar(
        version,
        EstadosTecho.EN_REVISION,
        usuario,
        EventoAuditoria.Accion.ENVIAR,
        f'Techo directivo v{version.numero} enviado a revisión',
    )


def observar(version, usuario, motivo):
    """EN_REVISION → OBSERVADO (con observaciones del revisor)."""
    if not (motivo or '').strip():
        raise ValidationError('Debe indicar el motivo de la observación.')
    version.observaciones = motivo
    version.save(update_fields=['observaciones', 'updated_at'])
    return _transicionar(
        version,
        EstadosTecho.OBSERVADO,
        usuario,
        EventoAuditoria.Accion.DEVOLVER,
        f'Techo directivo v{version.numero} observado: {motivo}',
    )


def aprobar(version, usuario):
    """EN_REVISION → APROBADO."""
    return _transicionar(
        version,
        EstadosTecho.APROBADO,
        usuario,
        EventoAuditoria.Accion.APROBAR,
        f'Techo directivo v{version.numero} aprobado',
    )


def _validar_fuentes_organismos(version):
    """Valida que fuentes/organismos/rubros presentes pertenezcan a la gestión."""
    gestion = version.ceiling.gestion
    for recurso in version.recursos.select_related(
        'rubro', 'fuente', 'organismo', 'entidad_otorgante',
    ).all():
        for nombre, valor in (
            ('Rubro', recurso.rubro),
            ('Fuente de financiamiento', recurso.fuente),
            ('Organismo financiador', recurso.organismo),
            ('Entidad otorgante', recurso.entidad_otorgante),
        ):
            if valor is not None and valor.gestion != gestion.anio:
                raise ValidationError(
                    f'{nombre} "{valor.codigo}" no pertenece a la gestión '
                    f'{gestion.anio} (recurso "{recurso.concepto}").'
                )
    for gasto in version.gastos_obligatorios.select_related(
        'fuente', 'organismo', 'objeto_gasto',
    ).all():
        for nombre, valor in (
            ('Fuente de financiamiento', gasto.fuente),
            ('Organismo financiador', gasto.organismo),
            ('Objeto del gasto', gasto.objeto_gasto),
        ):
            if valor is not None and valor.gestion != gestion.anio:
                raise ValidationError(
                    f'{nombre} "{valor.codigo}" no pertenece a la gestión '
                    f'{gestion.anio} (gasto "{gasto.denominacion}").'
                )


@transaction.atomic
def fijar_techo(version, usuario, observaciones=''):
    """APROBADO → FIJADO con las validaciones del §24.

    Valida: gestión habilitada (`validar_gestion_para_techo`), montos >= 0,
    sumatorias correctas (distribuible = bruto − obligatorios >= 0) y
    fuentes/organismos válidos si están presentes. Congela la versión
    (inmutable + checksum) y actualiza `version_actual`/estado del techo.
    """
    ceiling = version.ceiling
    validar_gestion_para_techo(ceiling.gestion)

    comp = composicion_techo(ceiling)
    if comp['techo_distribuible'] < 0:
        raise ValidationError(
            'Los gastos obligatorios superan el techo bruto: '
            f'obligatorios {comp["gastos_obligatorios"]} > bruto '
            f'{comp["techo_bruto"]}.'
        )
    negativos = [
        r for r in version.recursos.all() if r.monto < 0
    ] + [g for g in version.gastos_obligatorios.all() if g.monto < 0]
    if negativos:
        raise ValidationError(
            'Existen montos negativos; corrija antes de fijar el techo.'
        )
    _validar_fuentes_organismos(version)

    estado_previo = version.estado
    if estado_previo != EstadosTecho.APROBADO:
        if estado_previo not in EstadosTecho.TRANSICIONES.get(
            EstadosTecho.APROBADO, set()
        ):
            raise ValidationError(
                'Solo un techo aprobado puede fijarse '
                f'(estado actual: {version.get_estado_display()}).'
            )

    version.fijar(usuario, observaciones)
    ceiling.version_actual = version.numero
    ceiling.estado = EstadosTecho.FIJADO
    ceiling.save(update_fields=['version_actual', 'estado', 'updated_at'])
    registrar_evento(
        usuario,
        EventoAuditoria.Accion.APROBAR,
        'DirectiveCeilingVersion',
        version.id,
        version=version.numero,
        resumen=(
            f'Techo directivo fijado v{version.numero} '
            f'(gestión {ceiling.gestion.anio})'
        ),
        datos_previos={'estado': estado_previo},
        datos_posteriores={
            'estado': EstadosTecho.FIJADO,
            'hash': version.hash,
            'fecha_fijacion': version.fecha_fijacion.isoformat(),
        },
        gestion=ceiling.gestion.anio,
    )
    return version


@transaction.atomic
def ajuste_de_techo(ceiling, usuario):
    """§25 — Ajuste post-fijación: crea una VERSIÓN NUEVA desde la fijada.

    La versión fijada queda intacta (solo lectura, inmutable). La nueva
    versión (numero = actual + 1) parte de BORRADOR copiando recursos y gastos
    obligatorios de la fijada para ser editada; `version_actual` y el estado
    del techo se mueven a la versión nueva.
    """
    anterior = obtener_version_actual(ceiling)
    if anterior is None or anterior.estado != EstadosTecho.FIJADO:
        raise ValidationError(
            'Solo se puede ajustar un techo que esté fijado '
            f'(estado actual: {anterior.estado if anterior else "sin versión"}).'
        )

    nuevo_numero = ceiling.version_actual + 1
    nueva = DirectiveCeilingVersion.objects.create(
        ceiling=ceiling,
        numero=nuevo_numero,
        estado=EstadosTecho.BORRADOR,
        observaciones=f'Ajuste de la versión {anterior.numero} (fijada).',
        created_by=usuario,
        updated_by=usuario,
    )
    for r in anterior.recursos.all():
        CeilingResource.objects.create(
            version=nueva, origen=r.origen, rubro=r.rubro, fuente=r.fuente,
            organismo=r.organismo, entidad_otorgante=r.entidad_otorgante,
            concepto=r.concepto, monto=r.monto, documento=r.documento,
            created_by=usuario, updated_by=usuario,
        )
    for g in anterior.gastos_obligatorios.all():
        MandatoryExpense.objects.create(
            version=nueva, da=g.da, ue=g.ue, programa=g.programa,
            actividad=g.actividad, denominacion=g.denominacion, fuente=g.fuente,
            organismo=g.organismo, objeto_gasto=g.objeto_gasto,
            entidad_transferencia=g.entidad_transferencia, monto=g.monto,
            documento=g.documento, created_by=usuario, updated_by=usuario,
        )
    ceiling.version_actual = nuevo_numero
    ceiling.estado = EstadosTecho.BORRADOR
    ceiling.save(update_fields=['version_actual', 'estado', 'updated_at'])
    registrar_evento(
        usuario,
        EventoAuditoria.Accion.CREAR,
        'DirectiveCeilingVersion',
        nueva.id,
        version=nuevo_numero,
        resumen=(
            f'Ajuste de techo: versión {nuevo_numero} creada desde la fijada '
            f'{anterior.numero} (gestión {ceiling.gestion.anio})'
        ),
        datos_previos={'version': anterior.numero, 'estado': anterior.estado},
        datos_posteriores={'version': nuevo_numero, 'estado': nueva.estado},
        gestion=ceiling.gestion.anio,
    )
    return nueva


# ===========================================================================
# Fase 4 — Distribución presupuestaria
# ===========================================================================

class ErrorDisponibilidad(ValidationError):
    """Saldo insuficiente por fuente: ValidationError con código
    BUDGET_EXCEEDED y `details` estructurados (requested/available/
    difference) para la respuesta 400 de la API."""

    def __init__(self, fuente_id, requested, available):
        self.details = {
            'fuente': str(fuente_id),
            'requested': str(requested),
            'available': str(available),
            'difference': str(requested - available),
        }
        super().__init__(
            f'El monto solicitado supera el saldo disponible de la fuente '
            f'({requested} > {available}).',
            code='BUDGET_EXCEEDED',
        )


class ErrorObjetoGastoExcedido(ValidationError):
    """Programación por objeto del gasto que excede el disponible de la
    apertura (§91): ValidationError con código BUDGET_EXCEEDED y `details`
    {requested, available, difference} — la API la mapea a HTTP 409.

    A diferencia de `ErrorDisponibilidad` (por fuente), esta excepción NO
    lleva `fuente`: el exceso es contra el techo de la APERTURA (§90-91).
    """

    def __init__(self, requested, available):
        self.details = {
            'requested': str(requested),
            'available': str(available),
            'difference': str(requested - available),
        }
        super().__init__(
            f'El monto solicitado supera el disponible de la apertura '
            f'({requested} > {available}).',
            code='BUDGET_EXCEEDED',
        )


def validar_gestion_para_distribucion(gestion):
    """Valida que la gestión esté habilitada para operar la distribución."""
    if not gestion_habilitada(gestion):
        raise ValidationError(
            f'La gestión {gestion.anio} no está habilitada para la '
            f'distribución presupuestaria '
            f'(estado actual: {gestion.get_estado_display()}).'
        )
    return True


def _version_techo_fijada(gestion):
    """Última versión FIJADA del techo directivo de la gestión; None si no hay."""
    ceiling = DirectiveCeiling.objects.filter(gestion=gestion).first()
    if ceiling is None:
        return None
    return (
        DirectiveCeilingVersion.objects
        .filter(ceiling=ceiling, estado=EstadosTecho.FIJADO)
        .order_by('-numero')
        .first()
    )


def techo_distribuible_por_fuente(gestion):
    """Techo distribuible por fuente de financiamiento: {fuente_id: monto}.

    Se calcula desde la última versión FIJADA del techo directivo:
    techo[f] = Σ recursos[f] − Σ gastos obligatorios[f] (gastos atribuidos a
    esa fuente). Los recursos/gastos sin fuente no son distribuibles en esta
    fase. Sin techo fijado devuelve {} y las operaciones de distribución se
    BLOQUEAN. Montos Decimal, nunca float.
    """
    version = _version_techo_fijada(gestion)
    if version is None:
        return {}
    montos = {}
    for r in version.recursos.exclude(fuente_id__isnull=True):
        montos[r.fuente_id] = montos.get(r.fuente_id, Decimal('0.00')) + r.monto
    for g in version.gastos_obligatorios.exclude(fuente_id__isnull=True):
        montos[g.fuente_id] = montos.get(g.fuente_id, Decimal('0.00')) - g.monto
    return montos


def _distribuido_por_fuente(gestion, excluir_allocation_id=None):
    """Σ AllocationSource por fuente (excluye aperturas CERRADAS)."""
    qs = (
        AllocationSource.objects
        .filter(allocation__gestion=gestion)
        .exclude(allocation__estado=EstadoApertura.CERRADA)
        .exclude(fuente_id__isnull=True)
    )
    if excluir_allocation_id is not None:
        qs = qs.exclude(allocation_id=excluir_allocation_id)
    return {
        fila['fuente_id']: fila['total']
        for fila in qs.values('fuente_id').annotate(total=models.Sum('monto'))
    }


def distribuido_por_fuente(gestion):
    """{fuente_id: monto} distribuido por aperturas (sin CERRADAS)."""
    return _distribuido_por_fuente(gestion)


def reservado_por_fuente(gestion):
    """{fuente_id: monto} reservado (reservas ACTIVAS)."""
    qs = (
        Reserve.objects
        .filter(gestion=gestion, estado=EstadoReserva.ACTIVA)
        .exclude(fuente_id__isnull=True)
    )
    return {
        fila['fuente_id']: fila['total']
        for fila in qs.values('fuente_id').annotate(total=models.Sum('monto'))
    }


def _disponible_por_fuente(gestion, excluir_allocation_id=None):
    """techo − distribuido − reservado por fuente (solo fuentes del techo).

    Sin techo fijado devuelve {} (distribución bloqueada).
    """
    techo = techo_distribuible_por_fuente(gestion)
    if not techo:
        return {}
    distribuido = _distribuido_por_fuente(gestion, excluir_allocation_id)
    reservado = reservado_por_fuente(gestion)
    return {
        fid: (
            techo.get(fid, Decimal('0.00'))
            - distribuido.get(fid, Decimal('0.00'))
            - reservado.get(fid, Decimal('0.00'))
        )
        for fid in techo
    }


def disponible_por_fuente(gestion):
    """{fuente_id: monto} disponible para distribuir/reservar."""
    return _disponible_por_fuente(gestion)


@transaction.atomic
def version_distribucion_activa(gestion):
    """Versión vigente de la distribución: la no fijada de mayor número.

    Si no existe (primer uso) crea la versión 1 en BORRADOR. Si la última
    versión está FIJADA (inmutable) NO auto-crea: la distribución quedó
    congelada y solo un `ajuste_distribucion` explícito abre la versión
    siguiente (Fase 7, §51: ajuste posterior = versión nueva).
    """
    activa = (
        DistributionVersion.objects
        .filter(gestion=gestion, inmutable=False)
        .order_by('-numero')
        .first()
    )
    if activa is not None:
        return activa
    fijada = (
        DistributionVersion.objects
        .filter(gestion=gestion, inmutable=True)
        .order_by('-numero')
        .first()
    )
    if fijada is not None:
        raise ValidationError(
            'La distribución está fijada (inmutable); use un ajuste para '
            'crear la versión siguiente.'
        )
    return DistributionVersion.objects.create(gestion=gestion, numero=1)


def _bloquear_fuentes(gestion, fuente_ids):
    """select_for_update sobre las filas de recurso de las fuentes.

    Implementación central en `control.BudgetControlService._bloquear_fuentes`
    (Fase 8): el control financiero vive en `control.py`. Las filas del techo
    FIJADO son inmutables; el lock serializa las validaciones de
    disponibilidad concurrentes sobre la misma fuente (el segundo request
    re-lee los agregados ya commiteados).
    """
    from .control import BudgetControlService
    BudgetControlService._bloquear_fuentes(gestion, fuente_ids)


def _validar_fuentes_ingresadas(fuentes):
    """Valida la lista [{fuente, organismo, monto}] y resuelve los UUID."""
    if not isinstance(fuentes, (list, tuple)) or not fuentes:
        raise ValidationError(
            'Debe indicar al menos una fuente de financiamiento '
            '({fuente, organismo, monto}).'
        )
    from apps.catalogos.models import (
        FuenteFinanciamiento,
        OrganismoFinanciador,
    )
    validas = []
    for fila in fuentes:
        monto = fila.get('monto')
        if monto is None or monto <= 0:
            raise ValidationError(
                'El monto de cada fuente debe ser mayor que 0.'
            )
        fuente_id = fila.get('fuente')
        if not fuente_id:
            raise ValidationError(
                'Cada asignación debe indicar una fuente de financiamiento.'
            )
        organismo_id = fila.get('organismo')
        validas.append((fuente_id, organismo_id, monto))
    fuente_ids = {f for f, _, _ in validas}
    existentes = set(
        FuenteFinanciamiento.objects
        .filter(id__in=fuente_ids).values_list('id', flat=True)
    )
    faltantes = fuente_ids - existentes
    if faltantes:
        raise ValidationError(
            f'Fuente(s) de financiamiento inexistente(s): {faltantes}'
        )
    organismo_ids = {o for _, o, _ in validas if o}
    if organismo_ids:
        existentes_o = set(
            OrganismoFinanciador.objects
            .filter(id__in=organismo_ids).values_list('id', flat=True)
        )
        faltantes_o = organismo_ids - existentes_o
        if faltantes_o:
            raise ValidationError(
                f'Organismo(s) financiador(es) inexistente(s): {faltantes_o}'
            )
    return validas


@transaction.atomic
def crear_allocation(gestion, usuario, datos):
    """Crea una apertura programática con sus fuentes en UNA transacción.

    Valida gestión habilitada y disponibilidad por fuente contra el techo
    fijado (BUDGET_EXCEEDED con requested/available/difference); la versión
    activa de distribución se crea si no existe. La disponibilidad se
    consulta en `BudgetControlService.get_available_for_distribution`
    (control.py, Fase 8). Registra auditoría.
    """
    validar_gestion_para_distribucion(gestion)
    techo = techo_distribuible_por_fuente(gestion)
    if not techo:
        raise ValidationError(
            f'La gestión {gestion.anio} no tiene un techo directivo fijado; '
            'la distribución está bloqueada.'
        )
    version = version_distribucion_activa(gestion)

    fuentes = datos.pop('fuentes', None)
    validas = _validar_fuentes_ingresadas(fuentes)
    _bloquear_fuentes(gestion, {f for f, _, _ in validas})
    from .control import BudgetControlService
    disponible = BudgetControlService.get_available_for_distribution(gestion)
    for fuente_id, _, monto in validas:
        saldo = disponible.get(fuente_id, Decimal('0.00'))
        if monto > saldo:
            raise ErrorDisponibilidad(fuente_id, monto, saldo)

    allocation = Allocation.objects.create(
        gestion=gestion,
        version=version,
        estado=EstadoApertura.ACTIVA,
        created_by=usuario,
        updated_by=usuario,
        **datos,
    )
    for fuente_id, organismo_id, monto in validas:
        AllocationSource.objects.create(
            allocation=allocation,
            fuente_id=fuente_id,
            organismo_id=organismo_id,
            monto=monto,
            created_by=usuario,
            updated_by=usuario,
        )
    registrar_evento(
        usuario,
        EventoAuditoria.Accion.CREAR,
        'Allocation',
        allocation.id,
        resumen=(
            f'Apertura "{allocation.denominacion}" creada '
            f'(gestión {gestion.anio}, versión de distribución v{version.numero})'
        ),
        datos_posteriores={
            'denominacion': allocation.denominacion,
            'total': str(allocation.total),
            'fuentes': [
                {'fuente': str(f), 'organismo': str(o), 'monto': str(m)}
                for f, o, m in validas
            ],
        },
        gestion=gestion.anio,
    )
    return allocation


@transaction.atomic
def actualizar_allocation(allocation, usuario, datos):
    """Actualiza una apertura (datos + reemplazo de fuentes) en transacción.

    Bloqueada si la apertura está CERRADA o su versión de distribución es
    inmutable. La disponibilidad se valida excluyendo los montos actuales de
    la propia apertura (permite subas/rebajas). Registra auditoría.
    """
    validar_gestion_para_distribucion(allocation.gestion)
    if allocation.estado == EstadoApertura.CERRADA:
        raise ValidationError(
            'No se puede modificar una apertura cerrada.'
        )
    version = allocation.version
    if version is not None and version.inmutable:
        raise ValidationError(
            'La versión de distribución está fijada (inmutable); '
            'no se puede modificar la apertura.'
        )

    estado_previo = {
        'denominacion': allocation.denominacion,
        'estado': allocation.estado,
        'fuentes': [
            {'fuente': str(s.fuente_id or ''), 'monto': str(s.monto)}
            for s in allocation.fuentes.all()
        ],
    }

    fuentes = datos.pop('fuentes', None)
    validas = None
    if fuentes is not None:
        validas = _validar_fuentes_ingresadas(fuentes)
        _bloquear_fuentes(allocation.gestion, {f for f, _, _ in validas})
        disponible = _disponible_por_fuente(
            allocation.gestion, excluir_allocation_id=allocation.id,
        )
        for fuente_id, _, monto in validas:
            saldo = disponible.get(fuente_id, Decimal('0.00'))
            if monto > saldo:
                raise ErrorDisponibilidad(fuente_id, monto, saldo)

    campos = (
        'unidad_organizacional', 'distrito', 'da', 'ue', 'categoria',
        'proyecto_codigo', 'codigo_sisin', 'actividad_codigo',
        'denominacion', 'tipo_apertura', 'orden',
    )
    for campo in campos:
        if campo in datos:
            setattr(allocation, campo, datos[campo])
    allocation.updated_by = usuario
    allocation.save()

    if validas is not None:
        allocation.fuentes.all().delete()
        for fuente_id, organismo_id, monto in validas:
            AllocationSource.objects.create(
                allocation=allocation,
                fuente_id=fuente_id,
                organismo_id=organismo_id,
                monto=monto,
                created_by=usuario,
                updated_by=usuario,
            )

    registrar_evento(
        usuario,
        EventoAuditoria.Accion.MODIFICAR,
        'Allocation',
        allocation.id,
        resumen=f'Apertura "{allocation.denominacion}" modificada '
                f'(gestión {allocation.gestion.anio})',
        datos_previos=estado_previo,
        datos_posteriores={
            'denominacion': allocation.denominacion,
            'fuentes': [
                {'fuente': str(s.fuente_id or ''), 'monto': str(s.monto)}
                for s in allocation.fuentes.all()
            ],
        },
        gestion=allocation.gestion.anio,
    )
    return allocation


@transaction.atomic
def eliminar_allocation(allocation, usuario):
    """Elimina una apertura; solo BORRADOR/ACTIVA (no cerradas).

    Guard de inmutabilidad (Fase 7): rechazada si la apertura pertenece a
    una versión de distribución fijada.
    """
    if allocation.estado == EstadoApertura.CERRADA:
        raise ValidationError('No se puede eliminar una apertura cerrada.')
    if allocation.version is not None and allocation.version.inmutable:
        raise ValidationError(
            'La versión de distribución está fijada (inmutable); '
            'no se puede eliminar la apertura.'
        )
    gestion_anio = allocation.gestion.anio
    denominacion = allocation.denominacion
    allocation.delete()
    registrar_evento(
        usuario,
        EventoAuditoria.Accion.ANULAR,
        'Allocation',
        allocation.id,
        resumen=f'Apertura "{denominacion}" eliminada (gestión {gestion_anio})',
        gestion=gestion_anio,
    )


@transaction.atomic
def cerrar_allocation(allocation, usuario):
    """Cierra una apertura (estado CERRADA) si no excede el disponible.

    Revalida cada fuente contra el disponible excluyendo la propia apertura
    (guard de consistencia "solo si no excede"). Una apertura cerrada no
    puede editarse ni eliminarse. Registra auditoría.
    """
    if allocation.estado == EstadoApertura.CERRADA:
        raise ValidationError('La apertura ya está cerrada.')
    validar_gestion_para_distribucion(allocation.gestion)
    _bloquear_fuentes(
        allocation.gestion,
        {s.fuente_id for s in allocation.fuentes.all() if s.fuente_id},
    )
    disponible = _disponible_por_fuente(
        allocation.gestion, excluir_allocation_id=allocation.id,
    )
    for fuente in allocation.fuentes.all():
        if fuente.fuente_id is None:
            continue
        saldo = disponible.get(fuente.fuente_id, Decimal('0.00'))
        if fuente.monto > saldo:
            raise ErrorDisponibilidad(fuente.fuente_id, fuente.monto, saldo)

    allocation.estado = EstadoApertura.CERRADA
    allocation.updated_by = usuario
    allocation.save(update_fields=['estado', 'updated_by', 'updated_at'])
    registrar_evento(
        usuario,
        EventoAuditoria.Accion.CERRAR,
        'Allocation',
        allocation.id,
        resumen=f'Apertura "{allocation.denominacion}" cerrada '
                f'(gestión {allocation.gestion.anio})',
        datos_posteriores={'estado': EstadoApertura.CERRADA},
        gestion=allocation.gestion.anio,
    )
    return allocation


@transaction.atomic
def crear_reserva(gestion, usuario, datos):
    """Crea una reserva ACTIVA sobre una fuente (decrece el disponible).

    Fase 8: delega en `BudgetControlService.reserve` (control.py), el núcleo
    financiero transaccional (lock sobre el techo fijado + BUDGET_EXCEEDED).
    """
    from .control import BudgetControlService
    return BudgetControlService.reserve(
        gestion,
        fuente=datos.get('fuente'),
        organismo=datos.get('organismo'),
        monto=datos.get('monto'),
        motivo=datos.get('motivo', ''),
        usuario=usuario,
        tipo=datos.get('tipo') or TipoReserva.OTRA,
    )


@transaction.atomic
def liberar_reserva(reserva, usuario):
    """Libera una reserva ACTIVA (estado LIBERADA); devuelve el disponible.

    Guard de inmutabilidad (Fase 7): una reserva de una versión de
    distribución fijada no puede liberarse (cambiaría el estado congelado).
    Fase 8: delega en `BudgetControlService.release` (control.py).
    """
    from .control import BudgetControlService
    return BudgetControlService.release(reserva, usuario)


def resumen_distribucion(gestion):
    """Resumen del dashboard de distribución (§48): cards + tabla por fuente.

    Totales = agregaciones, nunca filas en BD. Los montos son Decimal
    (el borde API los serializa a str); `porcentaje` es float (0-100).
    Consistencia: techo = distribuido + reservado + disponible exacto.
    """
    from apps.catalogos.models import FuenteFinanciamiento

    techo = techo_distribuible_por_fuente(gestion)
    distribuido = distribuido_por_fuente(gestion)
    reservado = reservado_por_fuente(gestion)
    disponible = _disponible_por_fuente(gestion)

    fuente_ids = set(techo) | set(distribuido) | set(reservado)
    fuentes = {
        f.id: f
        for f in FuenteFinanciamiento.objects.filter(id__in=fuente_ids)
    } if fuente_ids else {}

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
        disp = disponible.get(fid, Decimal('0.00'))
        total_techo += t
        total_distribuido += d
        total_reservado += r
        total_disponible += disp
        por_fuente.append({
            'fuente_id': str(fid),
            'denominacion': fuentes[fid].denominacion if fid in fuentes else '-',
            'techo': t,
            'distribuido': d,
            'reservado': r,
            'disponible': disp,
            'porcentaje': round(float(d / t * 100), 2) if t else 0.0,
        })

    porcentaje = (
        round(float(total_distribuido / total_techo * 100), 2)
        if total_techo else 0.0
    )
    return {
        'gestion': gestion.anio,
        'techo_distribuible': total_techo,
        'distribuido': total_distribuido,
        'reservado': total_reservado,
        'disponible': total_disponible,
        'porcentaje': porcentaje,
        'aperturas_count': (
            Allocation.objects
            .filter(gestion=gestion)
            .exclude(estado=EstadoApertura.CERRADA)
            .count()
        ),
        'por_fuente': por_fuente,
    }


# ===========================================================================
# Fase 7 — Fijación de la distribución: validación Σfuente, checksum,
# máquina de estados de la versión e inmutabilidad (§49-52, §132-133).
# ===========================================================================

# Tolerancia de redondeo: |diferencia| <= 0.01 se considera 0. Los montos
# viven con 2 decimales (NUMERIC(18,2)); la tolerancia documenta el centavo
# residual de operaciones de redondeo previas y evita rechazos espurios.
UMBRAL_DIFERENCIA = Decimal('0.01')


def _redondear_monto(valor):
    """Decimal a 2 decimales (ROUND_HALF_UP), convención de la BD."""
    return valor.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


def validar_distribucion_completa(gestion):
    """Valida que la distribución esté completa por FF/OF (§49-52).

    Para CADA fuente del techo fijado:
        diferencia = techo_distribuible − (distribuido + reservado)
    `distribuido`/`reservado` usan los agregados existentes
    (`distribuido_por_fuente`/`reservado_por_fuente`: aperturas no CERRADAS
    y reservas ACTIVAS, respectivamente). |diferencia| <= 0.01 se tolera
    como 0 (redondeo a 2 decimales). Sin techo fijado devuelve valida=True
    con lista vacía (no hay fuentes que diferir; la distribución igual
    queda bloqueada por techo en las operaciones de escritura).
    """
    from apps.catalogos.models import FuenteFinanciamiento

    techo = techo_distribuible_por_fuente(gestion)
    distribuido = distribuido_por_fuente(gestion)
    reservado = reservado_por_fuente(gestion)

    fuente_ids = set(techo)
    fuentes = (
        {f.id: f for f in FuenteFinanciamiento.objects.filter(id__in=fuente_ids)}
        if fuente_ids else {}
    )

    diferencias = []
    for fid in sorted(
        fuente_ids,
        key=lambda x: (fuentes[x].codigo if x in fuentes else ''),
    ):
        t = _redondear_monto(techo.get(fid, Decimal('0.00')))
        d = _redondear_monto(distribuido.get(fid, Decimal('0.00')))
        r = _redondear_monto(reservado.get(fid, Decimal('0.00')))
        diferencia = t - d - r
        if abs(diferencia) <= UMBRAL_DIFERENCIA:
            diferencia = Decimal('0.00')
        diferencias.append({
            'fuente_id': str(fid),
            'denominacion': fuentes[fid].denominacion if fid in fuentes else '-',
            'techo': t,
            'distribuido': d,
            'reservado': r,
            'diferencia': diferencia,
        })

    valida = all(d['diferencia'] == 0 for d in diferencias)
    return {'valida': valida, 'diferencias': diferencias}


def checksum_distribucion(version):
    """SHA-256 de los datos semánticos de la versión de distribución.

    Incluye (fuente, organismo, monto) de las asignaciones de las APERTURAS
    ACTIVAS de la versión y las reservas de la versión. El payload se ordena
    por CONTENIDO semántico (no por ids de fila): el hash es estable ante
    reordenaciones de filas con el mismo conjunto de datos (patrón
    `DirectiveCeilingVersion`/Fase 2). Es la ÚNICA implementación del
    checksum (el modelo delega en esta función).
    """
    asignaciones = sorted(
        [
            (
                str(s.fuente_id or ''),
                str(s.organismo_id or ''),
                str(s.monto),
            )
            for s in AllocationSource.objects.filter(
                allocation__version=version,
                allocation__estado=EstadoApertura.ACTIVA,
            )
        ],
        key=lambda t: (t[0], t[1], t[2]),
    )
    reservas = sorted(
        [
            (
                str(r.fuente_id or ''),
                str(r.organismo_id or ''),
                r.tipo,
                r.estado,
                str(r.monto),
            )
            for r in version.reservas.all()
        ],
        key=lambda t: (t[0], t[1], t[2], t[3], t[4]),
    )
    payload = {'asignaciones': asignaciones, 'reservas': reservas}
    return hashlib.sha256(
        json.dumps(payload, ensure_ascii=False, sort_keys=True)
        .encode('utf-8')
    ).hexdigest()


def _transicionar_distribucion(version, destino, usuario, accion, resumen):
    """Aplica una transición válida de la versión y registra auditoría."""
    if version.inmutable:
        raise ValidationError(
            'La versión de distribución está fijada (inmutable); '
            'no puede transicionar.'
        )
    if version.estado == destino:
        raise ValidationError(
            f'La versión ya está en estado {version.get_estado_display()}.'
        )
    if destino not in EstadosTecho.TRANSICIONES.get(version.estado, set()):
        raise ValidationError(
            f'No se puede pasar la versión de '
            f'{version.get_estado_display()} a '
            f'{dict(EstadosTecho.CHOICES)[destino]}.'
        )
    estado_previo = version.estado
    version.estado = destino
    version.save(update_fields=['estado', 'updated_at'])
    registrar_evento(
        usuario,
        accion,
        'DistributionVersion',
        version.id,
        version=version.numero,
        resumen=resumen,
        datos_previos={'estado': estado_previo},
        datos_posteriores={'estado': version.estado},
        gestion=version.gestion.anio,
    )
    return version


def enviar_distribucion_a_revision(version, usuario):
    """BORRADOR|OBSERVADO → EN_REVISION."""
    return _transicionar_distribucion(
        version,
        EstadosTecho.EN_REVISION,
        usuario,
        EventoAuditoria.Accion.ENVIAR,
        f'Distribución v{version.numero} enviada a revisión',
    )


def observar_distribucion(version, usuario, motivo):
    """EN_REVISION → OBSERVADO (con observaciones del revisor)."""
    if not (motivo or '').strip():
        raise ValidationError('Debe indicar el motivo de la observación.')
    version.observaciones = motivo
    version.save(update_fields=['observaciones', 'updated_at'])
    return _transicionar_distribucion(
        version,
        EstadosTecho.OBSERVADO,
        usuario,
        EventoAuditoria.Accion.DEVOLVER,
        f'Distribución v{version.numero} observada: {motivo}',
    )


def aprobar_distribucion(version, usuario):
    """EN_REVISION → APROBADO."""
    return _transicionar_distribucion(
        version,
        EstadosTecho.APROBADO,
        usuario,
        EventoAuditoria.Accion.APROBAR,
        f'Distribución v{version.numero} aprobada',
    )


@transaction.atomic
def fijar_distribucion(version, usuario, observaciones=''):
    """APROBADO → FIJADO con validación Σfuente = techo (§49-52).

    Todo dentro de la transacción: la versión debe existir y estar APROBADA,
    la gestión habilitada y `validar_distribucion_completa` debe validar (si
    no → ValidationError listando las diferencias por fuente). Luego calcula
    el checksum y congela (inmutable, fecha, autor, observaciones); registra
    auditoría. Devuelve la versión fijada.
    """
    if version.estado != EstadosTecho.APROBADO:
        raise ValidationError(
            'Solo una distribución aprobada puede fijarse '
            f'(estado actual: {version.get_estado_display()}).'
        )
    if version.inmutable:
        raise ValidationError(
            'La versión de distribución ya está fijada (inmutable).'
        )
    validar_gestion_para_distribucion(version.gestion)

    validacion = validar_distribucion_completa(version.gestion)
    if not validacion['valida']:
        detalle = '; '.join(
            f'{d["denominacion"]} (techo {d["techo"]}, distribuido '
            f'{d["distribuido"]}, reservado {d["reservado"]}, diferencia '
            f'{d["diferencia"]})'
            for d in validacion['diferencias'] if d['diferencia'] != 0
        )
        raise ValidationError(
            'La distribución no está completa: diferencias por fuente '
            f'({detalle}).'
        )

    estado_previo = version.estado
    version.fijar(usuario, observaciones)
    registrar_evento(
        usuario,
        EventoAuditoria.Accion.APROBAR,
        'DistributionVersion',
        version.id,
        version=version.numero,
        resumen=(
            f'Distribución fijada v{version.numero} '
            f'(gestión {version.gestion.anio})'
        ),
        datos_previos={'estado': estado_previo},
        datos_posteriores={
            'estado': EstadosTecho.FIJADO,
            'hash': version.hash,
            'fecha_fijacion': version.fecha_fijacion.isoformat(),
        },
        gestion=version.gestion.anio,
    )
    return version


@transaction.atomic
def ajuste_distribucion(version, usuario):
    """Ajuste post-fijación (§51): crea una VERSIÓN NUEVA desde la fijada.

    La versión fijada queda intacta (histórico, inmutable, solo lectura).
    La nueva versión (numero + 1) nace en BORRADOR SIN copiar montos: la
    reformulación (Fase 10) define los cambios; acá solo se prepara el
    contenedor vacío para la distribución siguiente.
    """
    if version.estado != EstadosTecho.FIJADO or not version.inmutable:
        raise ValidationError(
            'Solo se puede ajustar una distribución fijada '
            f'(estado actual: {version.estado or "sin versión"}).'
        )

    nueva = DistributionVersion.objects.create(
        gestion=version.gestion,
        numero=version.numero + 1,
        estado=EstadosTecho.BORRADOR,
        observaciones=f'Ajuste de la versión {version.numero} (fijada).',
        created_by=usuario,
        updated_by=usuario,
    )
    registrar_evento(
        usuario,
        EventoAuditoria.Accion.CREAR,
        'DistributionVersion',
        nueva.id,
        version=nueva.numero,
        resumen=(
            f'Ajuste de distribución: versión {nueva.numero} creada desde '
            f'la fijada {version.numero} (gestión {version.gestion.anio})'
        ),
        datos_previos={'version': version.numero, 'estado': version.estado},
        datos_posteriores={'version': nueva.numero, 'estado': nueva.estado},
        gestion=version.gestion.anio,
    )
    return nueva


# ===========================================================================
# Fase 9 — Objetos del gasto: programación por apertura (§90-91)
# ===========================================================================


def _validar_allocation_programable(allocation):
    """Valida que la apertura exista, esté ACTIVA y su versión de
    distribución esté FIJADA; devuelve la instancia. Lanza ValidationError."""
    if not isinstance(allocation, Allocation):
        allocation = Allocation.objects.filter(pk=allocation).first()
    if allocation is None:
        raise ValidationError('La apertura no existe.')
    if allocation.estado != EstadoApertura.ACTIVA:
        raise ValidationError(
            f'La apertura está {allocation.get_estado_display()}; '
            'debe estar ACTIVA para programar.'
        )
    version = allocation.version
    if version is None or not version.inmutable or \
            version.estado != EstadosTecho.FIJADO:
        raise ValidationError(
            'La distribución debe estar fijada para programar objetos '
            'del gasto.'
        )
    return allocation


def _disponible_objeto_gasto(allocation, excluir_id=None):
    """Disponible de la apertura para objetos del gasto (Decimal, 0.00).

    techo de la apertura − Σ montos programados (excluyendo la fila
    `excluir_id` si se pasa, para actualizaciones de la propia fila).
    """
    from .control import BudgetControlService
    techo = BudgetControlService.get_allocation_ceiling(allocation)
    programado = (
        ExpenseObjectAllocation.objects
        .filter(allocation=allocation)
        .exclude(pk=excluir_id)
        .aggregate(total=models.Sum('monto'))['total']
    )
    return techo - (programado if programado is not None else Decimal('0.00'))


def _resolver_objeto_gasto(objeto_gasto_id):
    """Resuelve id o instancia de ObjetoGasto; None si no existe."""
    from apps.catalogos.models import ObjetoGasto
    if isinstance(objeto_gasto_id, ObjetoGasto):
        return objeto_gasto_id
    return ObjetoGasto.objects.filter(pk=objeto_gasto_id).first()


@transaction.atomic
def programar_objeto_gasto(allocation, objeto_gasto_id, monto, usuario):
    """Programa un objeto del gasto en una apertura (§90-91).

    Validaciones: apertura ACTIVA + versión de distribución FIJADA +
    objeto del gasto existente + monto >= 0. El disponible es techo −
    programado (excluyendo la fila si (allocation, objeto_gasto) ya
    existe: la operación es un UPSERT). Si monto > disponible lanza
    `ErrorObjetoGastoExcedido` (code BUDGET_EXCEEDED, details
    {requested, available, difference} → HTTP 409 en la API). Registra
    auditoría (crear/modificar). Devuelve la fila.
    """
    allocation = _validar_allocation_programable(allocation)
    objeto_gasto = _resolver_objeto_gasto(objeto_gasto_id)
    if objeto_gasto is None:
        raise ValidationError('El objeto del gasto no existe.')
    if monto is None or monto < 0:
        raise ValidationError('El monto debe ser mayor o igual a 0.')

    fila = ExpenseObjectAllocation.objects.filter(
        allocation=allocation, objeto_gasto=objeto_gasto,
    ).first()
    disponible = _disponible_objeto_gasto(
        allocation, excluir_id=fila.id if fila else None,
    )
    if monto > disponible:
        raise ErrorObjetoGastoExcedido(monto, disponible)

    if fila is None:
        fila = ExpenseObjectAllocation.objects.create(
            allocation=allocation, objeto_gasto=objeto_gasto, monto=monto,
            created_by=usuario, updated_by=usuario,
        )
        accion = EventoAuditoria.Accion.CREAR
    else:
        fila.monto = monto
        fila.updated_by = usuario
        fila.save(update_fields=['monto', 'updated_by', 'updated_at'])
        accion = EventoAuditoria.Accion.MODIFICAR
    registrar_evento(
        usuario,
        accion,
        'ExpenseObjectAllocation',
        fila.id,
        resumen=(
            f'Objeto del gasto {objeto_gasto.codigo} programado por {monto} '
            f'en la apertura {allocation.denominacion} '
            f'(gestión {allocation.gestion.anio})'
        ),
        datos_posteriores={
            'allocation': str(allocation.id),
            'objeto_gasto': objeto_gasto.codigo,
            'monto': str(monto),
        },
        gestion=allocation.gestion.anio,
    )
    return fila


@transaction.atomic
def actualizar_objeto_gasto(fila, monto, usuario):
    """Actualiza el monto de una programación (recalcula contra los demás).

    El disponible se recalcula EXCLUYENDO la fila actual (techo − Σ de los
    otros objetos); si el monto nuevo excede, lanza
    `ErrorObjetoGastoExcedido` (→ 409). Requiere apertura ACTIVA y versión
    de distribución FIJADA. Registra auditoría (modificar).
    """
    if not isinstance(fila, ExpenseObjectAllocation):
        fila = ExpenseObjectAllocation.objects.filter(pk=fila).first()
    if fila is None:
        raise ValidationError('La programación no existe.')
    _validar_allocation_programable(fila.allocation)
    if monto is None or monto < 0:
        raise ValidationError('El monto debe ser mayor o igual a 0.')

    disponible = _disponible_objeto_gasto(fila.allocation, excluir_id=fila.id)
    if monto > disponible:
        raise ErrorObjetoGastoExcedido(monto, disponible)

    monto_previo = fila.monto
    fila.monto = monto
    fila.updated_by = usuario
    fila.save(update_fields=['monto', 'updated_by', 'updated_at'])
    registrar_evento(
        usuario,
        EventoAuditoria.Accion.MODIFICAR,
        'ExpenseObjectAllocation',
        fila.id,
        resumen=(
            f'Objeto del gasto {fila.objeto_gasto.codigo} actualizado de '
            f'{monto_previo} a {monto} (apertura {fila.allocation.denominacion})'
        ),
        datos_previos={'monto': str(monto_previo)},
        datos_posteriores={'monto': str(monto)},
        gestion=fila.allocation.gestion.anio,
    )
    return fila


@transaction.atomic
def eliminar_objeto_gasto(fila, usuario):
    """Elimina una programación; libera el disponible de la apertura.

    Se puede eliminar libremente en esta fase (sin verificación de
    excedentes), siempre que la apertura esté ACTIVA y la versión de
    distribución FIJADA. Registra auditoría (anular).
    """
    if not isinstance(fila, ExpenseObjectAllocation):
        fila = ExpenseObjectAllocation.objects.filter(pk=fila).first()
    if fila is None:
        raise ValidationError('La programación no existe.')
    _validar_allocation_programable(fila.allocation)
    allocation = fila.allocation
    codigo = fila.objeto_gasto.codigo
    monto = fila.monto
    fila.delete()
    registrar_evento(
        usuario,
        EventoAuditoria.Accion.ANULAR,
        'ExpenseObjectAllocation',
        fila.id,
        resumen=(
            f'Objeto del gasto {codigo} ({monto}) eliminado de la apertura '
            f'{allocation.denominacion} (gestión {allocation.gestion.anio})'
        ),
        datos_previos={'monto': str(monto)},
        gestion=allocation.gestion.anio,
    )


# ===========================================================================
# Fase 10 — Reformulaciones presupuestarias (§92-97)
#
# Workflow de la cabecera: BORRADOR → EN_REVISION → OBSERVADA → APROBADA →
# APLICADA (o RECHAZADA desde EN_REVISION). El saldo efectivo de cada
# movimiento se registra con saldo_antes/saldo_despues y la aplicación es
# ATÓMICA: si un movimiento falla, la transacción completa hace rollback.
#
# DECISIÓN DE ARQUITECTURA (Fase 10, documentada):
#   La reformulación opera DIRECTAMENTE sobre las filas `AllocationSource`
#   existentes (no se duplican filas ni se re-apunta la versión de las
#   aperturas): el "nuevo saldo efectivo" ES el saldo tras el movimiento y
#   el histórico queda en `ReformMovement` + `EventoAuditoria`. La versión
#   fijada conserva sus filas (checksum de v1 queda obsoleto por diseño:
#   el congelamiento protege la EDICIÓN del documento, no los saldos que la
#   reformulación modifica legítimamente con trazabilidad). Si la
#   distribución está fijada y no hay versión activa, se abre la versión
#   siguiente vía `ajuste_distribucion` (contenedor BORRADOR que habilita
#   el flujo de la gestión; `version_resultante` se deja NULL en esta fase).
#   AJUSTE DE TECHO (modifica recursos, Fase 2) ≠ REFORMULACIÓN DE
#   DISTRIBUCIÓN (modifica cómo se distribuye; esta fase).
# ===========================================================================


def _resolver_allocation_de_gestion(gestion, allocation_id, campo):
    """Resuelve una apertura por id validando que pertenezca a la gestión."""
    allocation = (
        Allocation.objects.filter(pk=allocation_id, gestion=gestion).first()
        if allocation_id else None
    )
    if allocation_id and allocation is None:
        raise ValidationError(
            f'La apertura de {campo} no existe o no pertenece a la gestión '
            f'{gestion.anio}.'
        )
    return allocation


def _validar_movimientos_reform(gestion, movimientos):
    """Valida la estructura de los movimientos de una reformulación.

    Devuelve la lista normalizada de dicts {tipo, apertura_origen,
    apertura_destino, fuente, organismo, monto, motivo} (objetos resueltos).
    La disponibilidad de saldos NO se valida acá: se valida al aplicar
    (`aplicar_reform`), dentro de la transacción atómica.
    """
    if not isinstance(movimientos, (list, tuple)) or not movimientos:
        raise ValidationError(
            'Debe indicar al menos un movimiento de la reformulación.'
        )
    validos = []
    for i, fila in enumerate(movimientos):
        if not isinstance(fila, dict):
            raise ValidationError(
                f'Movimiento {i + 1}: debe ser un objeto con tipo, '
                'aperturas/fuente y monto.'
            )
        tipo = fila.get('tipo')
        tipos_validos = {t for t, _ in TipoMovimientoReform.CHOICES}
        if tipo not in tipos_validos:
            raise ValidationError(
                f'Movimiento {i + 1}: tipo inválido ({tipo}); debe ser uno '
                f'de {sorted(tipos_validos)}.'
            )
        monto = fila.get('monto')
        if monto is None or monto <= 0:
            raise ValidationError(
                f'Movimiento {i + 1}: el monto debe ser mayor que 0.'
            )
        monto = monto if isinstance(monto, Decimal) else Decimal(str(monto))

        origen = _resolver_allocation_de_gestion(
            gestion, fila.get('apertura_origen'), 'origen',
        )
        destino = _resolver_allocation_de_gestion(
            gestion, fila.get('apertura_destino'), 'destino',
        )
        if tipo in (TipoMovimientoReform.TRASPASO,):
            if origen is None or destino is None:
                raise ValidationError(
                    f'Movimiento {i + 1}: un traspaso requiere apertura de '
                    'origen y de destino.'
                )
        elif tipo == TipoMovimientoReform.INCREMENTO:
            if destino is None:
                raise ValidationError(
                    f'Movimiento {i + 1}: un incremento requiere apertura '
                    'de destino.'
                )
            if origen is not None:
                raise ValidationError(
                    f'Movimiento {i + 1}: un incremento no lleva apertura '
                    'de origen.'
                )
        elif tipo == TipoMovimientoReform.DISMINUCION:
            if origen is None:
                raise ValidationError(
                    f'Movimiento {i + 1}: una disminución requiere apertura '
                    'de origen.'
                )
            if destino is not None:
                raise ValidationError(
                    f'Movimiento {i + 1}: una disminución no lleva apertura '
                    'de destino.'
                )
        elif tipo == TipoMovimientoReform.CAMBIO_FUENTE:
            if origen is None:
                raise ValidationError(
                    f'Movimiento {i + 1}: un cambio de fuente requiere '
                    'apertura de origen.'
                )
            if destino is not None and destino.id != origen.id:
                raise ValidationError(
                    f'Movimiento {i + 1}: el cambio de fuente opera sobre la '
                    'MISMA apertura (apertura_destino debe omitirse o '
                    'coincidir con la de origen).'
                )

        # Fuente: obligatoria en todos los tipos (identifica el saldo).
        from apps.catalogos.models import FuenteFinanciamiento
        fuente_id = fila.get('fuente')
        if not fuente_id:
            raise ValidationError(
                f'Movimiento {i + 1}: debe indicar la fuente de '
                'financiamiento.'
            )
        fuente = FuenteFinanciamiento.objects.filter(pk=fuente_id).first()
        if fuente is None:
            raise ValidationError(
                f'Movimiento {i + 1}: la fuente de financiamiento no existe.'
            )
        if fuente.gestion != gestion.anio:
            raise ValidationError(
                f'Movimiento {i + 1}: la fuente "{fuente.codigo}" no '
                f'pertenece a la gestión {gestion.anio}.'
            )
        organismo = None
        organismo_id = fila.get('organismo')
        if organismo_id:
            from apps.catalogos.models import OrganismoFinanciador
            organismo = OrganismoFinanciador.objects.filter(
                pk=organismo_id,
            ).first()
            if organismo is None:
                raise ValidationError(
                    f'Movimiento {i + 1}: el organismo financiador no existe.'
                )
            if organismo.gestion != gestion.anio:
                raise ValidationError(
                    f'Movimiento {i + 1}: el organismo "{organismo.codigo}" '
                    f'no pertenece a la gestión {gestion.anio}.'
                )

        validos.append({
            'tipo': tipo,
            'apertura_origen': origen,
            'apertura_destino': destino,
            'fuente': fuente,
            'organismo': organismo,
            'monto': monto,
            'motivo': fila.get('motivo', '') or '',
        })
    return validos


@transaction.atomic
def crear_reform(gestion, tipo, motivo, usuario, movimientos):
    """Crea una reformulación en BORRADOR con sus movimientos (Fase 10).

    Valida la gestión habilitada, la existencia de una distribución FIJADA
    (las reformulaciones operan sobre sus aperturas) y la estructura de
    cada movimiento (aperturas/fuente de la gestión, monto > 0). La
    disponibilidad de saldos se valida recién al APLICAR. `version_origen`
    apunta a la versión fijada. Registra auditoría. Devuelve la reform.
    """
    validar_gestion_para_distribucion(gestion)
    tipos_validos = {t for t, _ in TipoReform.CHOICES}
    if tipo not in tipos_validos:
        raise ValidationError(
            f'Tipo de reformulación inválido ({tipo}); debe ser uno de '
            f'{sorted(tipos_validos)}.'
        )
    fijada = (
        DistributionVersion.objects
        .filter(gestion=gestion, inmutable=True)
        .order_by('-numero')
        .first()
    )
    if fijada is None:
        raise ValidationError(
            f'La gestión {gestion.anio} no tiene una distribución fijada; '
            'no se pueden crear reformulaciones.'
        )
    validos = _validar_movimientos_reform(gestion, movimientos)

    reform = Reform.objects.create(
        gestion=gestion,
        tipo=tipo,
        estado=EstadosReform.BORRADOR,
        motivo=motivo or '',
        version_origen=fijada,
        solicitada_por=usuario,
        created_by=usuario,
        updated_by=usuario,
    )
    for m in validos:
        ReformMovement.objects.create(
            reform=reform,
            tipo=m['tipo'],
            apertura_origen=m['apertura_origen'],
            apertura_destino=m['apertura_destino'],
            fuente=m['fuente'],
            organismo=m['organismo'],
            monto=m['monto'],
            motivo=m['motivo'],
            created_by=usuario,
            updated_by=usuario,
        )
    registrar_evento(
        usuario,
        EventoAuditoria.Accion.CREAR,
        'Reform',
        reform.id,
        resumen=(
            f'Reformulación {reform.get_tipo_display()} creada '
            f'(gestión {gestion.anio}, {len(validos)} movimiento(s))'
        ),
        datos_posteriores={
            'tipo': reform.tipo,
            'estado': reform.estado,
            'movimientos': len(validos),
        },
        gestion=gestion.anio,
    )
    return reform


def _transicionar_reform(reform, destino, usuario, accion, resumen,
                         estado_posterior_extra=None, update_extra=None):
    """Aplica una transición válida del workflow y registra auditoría."""
    if reform.estado == destino:
        raise ValidationError(
            f'La reformulación ya está en estado '
            f'{reform.get_estado_display()}.'
        )
    if destino not in EstadosReform.TRANSICIONES.get(reform.estado, set()):
        raise ValidationError(
            f'No se puede pasar la reformulación de '
            f'{reform.get_estado_display()} a '
            f'{dict(EstadosReform.CHOICES)[destino]}.'
        )
    estado_previo = reform.estado
    reform.estado = destino
    reform.updated_by = usuario
    update_fields = ['estado', 'updated_by', 'updated_at']
    if update_extra:
        update_fields += list(update_extra)
    reform.save(update_fields=update_fields)
    posterior = {'estado': reform.estado}
    if estado_posterior_extra:
        posterior.update(estado_posterior_extra)
    registrar_evento(
        usuario,
        accion,
        'Reform',
        reform.id,
        resumen=resumen,
        datos_previos={'estado': estado_previo},
        datos_posteriores=posterior,
        gestion=reform.gestion.anio,
    )
    return reform


def enviar_reform_a_revision(reform, usuario):
    """BORRADOR|OBSERVADA → EN_REVISION."""
    return _transicionar_reform(
        reform,
        EstadosReform.EN_REVISION,
        usuario,
        EventoAuditoria.Accion.ENVIAR,
        f'Reformulación enviada a revisión (gestión {reform.gestion.anio})',
    )


def observar_reform(reform, usuario, motivo):
    """EN_REVISION → OBSERVADA (con motivo del revisor, en auditoría)."""
    if not (motivo or '').strip():
        raise ValidationError('Debe indicar el motivo de la observación.')
    return _transicionar_reform(
        reform,
        EstadosReform.OBSERVADA,
        usuario,
        EventoAuditoria.Accion.DEVOLVER,
        f'Reformulación observada: {motivo} (gestión {reform.gestion.anio})',
    )


def aprobar_reform(reform, usuario):
    """EN_REVISION → APROBADA (registra al aprobador)."""
    reform.aprobada_por = usuario
    return _transicionar_reform(
        reform,
        EstadosReform.APROBADA,
        usuario,
        EventoAuditoria.Accion.APROBAR,
        f'Reformulación aprobada (gestión {reform.gestion.anio})',
        estado_posterior_extra={'aprobada_por': str(usuario.id)},
        update_extra=['aprobada_por'],
    )


def rechazar_reform(reform, usuario, motivo):
    """EN_REVISION → RECHAZADA (definitivo; no puede aplicarse).

    Se registra con accion `anular`: el rechazo anula el documento.
    """
    if not (motivo or '').strip():
        raise ValidationError('Debe indicar el motivo del rechazo.')
    return _transicionar_reform(
        reform,
        EstadosReform.RECHAZADA,
        usuario,
        EventoAuditoria.Accion.ANULAR,
        f'Reformulación rechazada: {motivo} (gestión {reform.gestion.anio})',
    )


# -- Movimientos de la aplicación (kernel financiero) -----------------------


def _lock_y_obtener_source(allocation, fuente_id, organismo_id, crear=False,
                           usuario=None):
    """AllocationSource (allocation, fuente, organismo) con lock de fila.

    Si `crear` y no existe, lo crea con monto 0.00 (el saldo inicial de un
    destino es 0; el monto del movimiento se SUMA después por el llamador —
    nunca se crea con el monto final). Devuelve (source|None, saldo_actual).
    """
    source = (
        AllocationSource.objects
        .select_for_update()
        .filter(
            allocation=allocation, fuente_id=fuente_id,
            organismo_id=organismo_id,
        )
        .first()
    )
    if source is None and crear:
        source = AllocationSource.objects.create(
            allocation=allocation, fuente_id=fuente_id,
            organismo_id=organismo_id, monto=Decimal('0.00'),
            created_by=usuario, updated_by=usuario,
        )
    saldo = source.monto if source is not None else Decimal('0.00')
    return source, saldo


def _incrementar_movimiento(reform, mov, usuario):
    """INCREMENTO: amplía el saldo del destino dentro de su techo de fuente.

    Regla §96 "el destino no excede el techo": el saldo RESULTANTE del
    AllocationSource destino no supera el techo distribuible de su fuente
    (`techo_distribuible_por_fuente`) → BUDGET_EXCEEDED si no. DECISIÓN
    documentada (Fase 10): la validación es por DESTINO contra el techo
    distribuible de la fuente, no contra el pool — tras una fijación el
    pool por fuente es 0 por construcción (Σ = techo − reservas), así que
    el pool solo crece con DISMINUCIONES/liberaciones; un incremento que
    cabe en el techo de la fuente es válido. Lock de la fuente
    (`_bloquear_fuentes`) + lock de la fila destino. Devuelve
    (saldo_antes, saldo_despues) del AllocationSource DESTINO.
    """
    from .control import BudgetControlService
    fuente_id = mov.fuente_id
    organismo_id = mov.organismo_id
    BudgetControlService._bloquear_fuentes(reform.gestion, {fuente_id})
    dest_src, saldo_antes = _lock_y_obtener_source(
        mov.apertura_destino, fuente_id, organismo_id,
        crear=True, usuario=usuario,
    )
    techo = techo_distribuible_por_fuente(reform.gestion)
    tope_fuente = techo.get(fuente_id, Decimal('0.00'))
    if saldo_antes + mov.monto > tope_fuente:
        raise ErrorDisponibilidad(
            fuente_id, mov.monto, tope_fuente - saldo_antes,
        )
    dest_src.monto = saldo_antes + mov.monto
    dest_src.updated_by = usuario
    dest_src.save(update_fields=['monto', 'updated_by', 'updated_at'])
    return saldo_antes, dest_src.monto


def _disminuir_movimiento(reform, mov, usuario):
    """DISMINUCION: devuelve saldo del origen al pool de la fuente.

    Valida saldo_origen >= monto (BUDGET_EXCEEDED si no); lock de la fuente
    + lock de la fila origen. Devuelve (saldo_antes, saldo_despues) del
    AllocationSource ORIGEN.
    """
    from .control import BudgetControlService
    fuente_id = mov.fuente_id
    organismo_id = mov.organismo_id
    BudgetControlService._bloquear_fuentes(reform.gestion, {fuente_id})
    origen_src, saldo_antes = _lock_y_obtener_source(
        mov.apertura_origen, fuente_id, organismo_id,
    )
    if mov.monto > saldo_antes:
        raise ErrorDisponibilidad(fuente_id, mov.monto, saldo_antes)
    origen_src.monto = saldo_antes - mov.monto
    origen_src.updated_by = usuario
    origen_src.save(update_fields=['monto', 'updated_by', 'updated_at'])
    return saldo_antes, origen_src.monto


def _cambio_fuente_movimiento(reform, mov, usuario):
    """CAMBIO_FUENTE: reduce la fuente vieja y aumenta la nueva (misma
    apertura, §96).

    La fuente VIEJA (a reducir) no se persiste en el modelo (una sola FK de
    fuente por movimiento): se infiere de forma determinista y documentada —
    el AllocationSource de la apertura distinto de (fuente nueva, organismo
    nuevo) con saldo suficiente para el monto; si hay varios, el de MAYOR
    saldo (empate → menor id). La fuente NUEVA crece validando la misma
    regla §96 del incremento: el saldo resultante del destino no supera el
    techo distribuible de la fuente nueva (BUDGET_EXCEEDED si no).
    Devuelve (saldo_antes, saldo_despues) de la fuente vieja.
    """
    from .control import BudgetControlService
    apertura = mov.apertura_origen
    fuente_nueva_id = mov.fuente_id
    organismo_nuevo_id = mov.organismo_id
    BudgetControlService._bloquear_fuentes(
        reform.gestion, {fuente_nueva_id},
    )

    candidatas = list(
        AllocationSource.objects
        .select_for_update()
        .filter(allocation=apertura)
        .exclude(
            fuente_id=fuente_nueva_id, organismo_id=organismo_nuevo_id,
        )
        .order_by('-monto', 'id')
    )
    origen_src = next(
        (s for s in candidatas if s.monto >= mov.monto), None,
    )
    if origen_src is None:
        raise ValidationError(
            'La apertura no tiene una fuente con saldo suficiente para el '
            'cambio de fuente.'
        )
    fuente_vieja_id = origen_src.fuente_id
    if fuente_vieja_id and fuente_vieja_id != fuente_nueva_id:
        BudgetControlService._bloquear_fuentes(
            reform.gestion, {fuente_vieja_id},
        )
    saldo_antes = origen_src.monto
    origen_src.monto = saldo_antes - mov.monto
    origen_src.updated_by = usuario
    origen_src.save(update_fields=['monto', 'updated_by', 'updated_at'])

    techo = techo_distribuible_por_fuente(reform.gestion)
    tope_fuente = techo.get(fuente_nueva_id, Decimal('0.00'))
    nueva_src, saldo_nueva = _lock_y_obtener_source(
        apertura, fuente_nueva_id, organismo_nuevo_id,
        crear=True, usuario=usuario,
    )
    if saldo_nueva + mov.monto > tope_fuente:
        raise ErrorDisponibilidad(
            fuente_nueva_id, mov.monto, tope_fuente - saldo_nueva,
        )
    nueva_src.monto = saldo_nueva + mov.monto
    nueva_src.updated_by = usuario
    nueva_src.save(update_fields=['monto', 'updated_by', 'updated_at'])
    return saldo_antes, origen_src.monto


def _aplicar_movimiento_reform(reform, mov, usuario):
    """Aplica UN movimiento dentro de la transacción de `aplicar_reform`.

    Registra saldo_antes/saldo_despues en el propio movimiento (histórico).
    Cualquier excepción propaga y hace rollback de TODO (atomicidad §97).
    """
    if mov.tipo == TipoMovimientoReform.TRASPASO:
        from .control import BudgetControlService
        resultado = BudgetControlService.apply_movement(
            mov.apertura_origen, mov.apertura_destino, mov.fuente,
            mov.organismo, mov.monto, mov.motivo, usuario,
        )
        saldo_antes, saldo_despues = (
            resultado['saldo_antes'], resultado['saldo_despues'],
        )
    elif mov.tipo == TipoMovimientoReform.INCREMENTO:
        saldo_antes, saldo_despues = _incrementar_movimiento(
            reform, mov, usuario,
        )
    elif mov.tipo == TipoMovimientoReform.DISMINUCION:
        saldo_antes, saldo_despues = _disminuir_movimiento(
            reform, mov, usuario,
        )
    elif mov.tipo == TipoMovimientoReform.CAMBIO_FUENTE:
        saldo_antes, saldo_despues = _cambio_fuente_movimiento(
            reform, mov, usuario,
        )
    else:
        raise ValidationError(
            f'Tipo de movimiento no aplicable ({mov.tipo}).'
        )
    mov.saldo_antes = saldo_antes
    mov.saldo_despues = saldo_despues
    mov.updated_by = usuario
    mov.save(update_fields=['saldo_antes', 'saldo_despues', 'updated_by',
                            'updated_at'])


@transaction.atomic
def aplicar_reform(reform, usuario):
    """APROBADA → APLICADA: aplica los movimientos en UNA transacción (§97).

    1. Valida estado APROBADA y gestión habilitada.
    2. Versión activa: si la distribución está FIJADA y no hay versión
       activa, abre la versión siguiente vía `ajuste_distribucion`
       (contenedor BORRADOR). DECISIÓN Fase 10 (documentada arriba): la
       reformulación opera DIRECTAMENTE sobre los AllocationSource/Reserve
       existentes — no se duplican filas; el "nuevo saldo efectivo" ES el
       saldo tras el movimiento y el histórico queda en `ReformMovement`
       + `EventoAuditoria`; `version_resultante` se deja NULL.
    3. Aplica cada movimiento en orden estable (orden de creación): TRASPASO
       (apply_movement, saldo_origen >= monto → BUDGET_EXCEEDED),
       INCREMENTO y CAMBIO_FUENTE (el destino no excede el techo
       distribuible de su fuente, §96) y DISMINUCION (saldo_origen >=
       monto), registrando saldo_antes/saldo_despues de cada
       AllocationSource afectado.
    4. Si CUALQUIER movimiento falla → ValidationError y ROLLBACK COMPLETO
       (nada se persiste: ni saldos, ni la versión abierta, ni el estado).
    5. Estado → APLICADA, fecha_aplicacion y auditoría.
    """
    if reform.estado != EstadosReform.APROBADA:
        raise ValidationError(
            'Solo una reformulación aprobada puede aplicarse '
            f'(estado actual: {reform.get_estado_display()}).'
        )
    validar_gestion_para_distribucion(reform.gestion)

    version_activa = (
        DistributionVersion.objects
        .filter(gestion=reform.gestion, inmutable=False)
        .order_by('-numero')
        .first()
    )
    if version_activa is None:
        fijada = (
            DistributionVersion.objects
            .filter(gestion=reform.gestion, inmutable=True)
            .order_by('-numero')
            .first()
        )
        if fijada is None:
            raise ValidationError(
                f'La gestión {reform.gestion.anio} no tiene una distribución '
                'fijada; no se puede aplicar la reformulación.'
            )
        version_activa = ajuste_distribucion(fijada, usuario)

    for mov in reform.movimientos.order_by('id'):
        _aplicar_movimiento_reform(reform, mov, usuario)

    estado_previo = reform.estado
    reform.estado = EstadosReform.APLICADA
    reform.fecha_aplicacion = timezone.now()
    reform.updated_by = usuario
    reform.save(update_fields=[
        'estado', 'fecha_aplicacion', 'updated_by', 'updated_at',
    ])
    registrar_evento(
        usuario,
        EventoAuditoria.Accion.APROBAR,
        'Reform',
        reform.id,
        resumen=(
            f'Reformulación {reform.get_tipo_display()} aplicada '
            f'(gestión {reform.gestion.anio}, '
            f'{reform.movimientos.count()} movimiento(s))'
        ),
        datos_previos={'estado': estado_previo},
        datos_posteriores={
            'estado': EstadosReform.APLICADA,
            'fecha_aplicacion': reform.fecha_aplicacion.isoformat(),
            'version_activa': version_activa.numero,
        },
        gestion=reform.gestion.anio,
    )
    return reform
