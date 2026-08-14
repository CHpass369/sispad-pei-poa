"""Servicios del ciclo presupuestario SIS-POA.

Fase 1 (gestión fiscal): bloqueos por gestión (§10 del prompt maestro) — las
fases 2+ validan el estado de la gestión a través de estas funciones antes de
operar (techo directivo, distribución, fijación, reformulaciones…).

Fase 2 (techo directivo): composición, ciclo de estados de la versión
(BORRADOR → EN_REVISION → APROBADO → FIJADO, con OBSERVADO), fijación inmutable
con checksum SHA-256 (§24-25) y ajustes por versión nueva (§25).

Estados del ciclo usados (nuevos códigos de `GestionFiscal.Estado`):
    CONFIGURACION → HABILITADA → EN_FORMULACION → VIGENTE → CERRADA
Los estados legacy se reconocen en los helpers para no romper la UI V1
(mapeo: preparacion≈CONFIGURACION, abierta≈HABILITADA,
formulacion≈EN_FORMULACION, cerrada≈CERRADA).
"""
from decimal import Decimal

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
    EstadosTecho,
    MandatoryExpense,
    Reserve,
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

    Si no existe (primer uso) crea la versión 1 en BORRADOR. La fijación
    completa llega en la Fase 7.
    """
    activa = (
        DistributionVersion.objects
        .filter(gestion=gestion, inmutable=False)
        .order_by('-numero')
        .first()
    )
    if activa is not None:
        return activa
    return DistributionVersion.objects.create(gestion=gestion, numero=1)


def _bloquear_fuentes(gestion, fuente_ids):
    """select_for_update sobre las filas de recurso de las fuentes.

    Las filas del techo FIJADO son inmutables; el lock serializa las
    validaciones de disponibilidad concurrentes sobre la misma fuente
    (el segundo request re-lee los agregados ya commiteados).
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
    activa de distribución se crea si no existe. Registra auditoría.
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
    disponible = _disponible_por_fuente(gestion)
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
    """Elimina una apertura; solo BORRADOR/ACTIVA (no cerradas)."""
    if allocation.estado == EstadoApertura.CERRADA:
        raise ValidationError('No se puede eliminar una apertura cerrada.')
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
    """Crea una reserva ACTIVA sobre una fuente (decrece el disponible)."""
    validar_gestion_para_distribucion(gestion)
    techo = techo_distribuible_por_fuente(gestion)
    if not techo:
        raise ValidationError(
            f'La gestión {gestion.anio} no tiene un techo directivo fijado; '
            'la distribución está bloqueada.'
        )
    version = version_distribucion_activa(gestion)

    fuente = datos.get('fuente')
    fuente_id = getattr(fuente, 'id', fuente)
    monto = datos.get('monto')
    if not fuente_id:
        raise ValidationError('Debe indicar la fuente de financiamiento.')
    if monto is None or monto <= 0:
        raise ValidationError('El monto de la reserva debe ser mayor que 0.')

    organismo = datos.get('organismo')
    organismo_id = getattr(organismo, 'id', organismo) if organismo else None

    _bloquear_fuentes(gestion, {fuente_id})
    disponible = _disponible_por_fuente(gestion)
    saldo = disponible.get(fuente_id, Decimal('0.00'))
    if monto > saldo:
        raise ErrorDisponibilidad(fuente_id, monto, saldo)

    reserva = Reserve.objects.create(
        gestion=gestion,
        version=version,
        fuente_id=fuente_id,
        organismo_id=organismo_id,
        tipo=datos.get('tipo') or TipoReserva.OTRA,
        motivo=datos.get('motivo', ''),
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
        resumen=f'Reserva {reserva.get_tipo_display()} de {monto} creada '
                f'(gestión {gestion.anio})',
        datos_posteriores={'monto': str(monto), 'tipo': reserva.tipo},
        gestion=gestion.anio,
    )
    return reserva


@transaction.atomic
def liberar_reserva(reserva, usuario):
    """Libera una reserva ACTIVA (estado LIBERADA); devuelve el disponible."""
    if reserva.estado == EstadoReserva.LIBERADA:
        raise ValidationError('La reserva ya está liberada.')
    reserva.estado = EstadoReserva.LIBERADA
    reserva.updated_by = usuario
    reserva.save(update_fields=['estado', 'updated_by', 'updated_at'])
    registrar_evento(
        usuario,
        EventoAuditoria.Accion.MODIFICAR,
        'Reserve',
        reserva.id,
        resumen=f'Reserva de {reserva.monto} liberada '
                f'(gestión {reserva.gestion.anio})',
        datos_previos={'estado': EstadoReserva.ACTIVA},
        datos_posteriores={'estado': EstadoReserva.LIBERADA},
        gestion=reserva.gestion.anio,
    )
    return reserva


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
