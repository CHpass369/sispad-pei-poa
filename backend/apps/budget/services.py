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
    CeilingResource,
    DirectiveCeiling,
    DirectiveCeilingVersion,
    EstadosTecho,
    MandatoryExpense,
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
