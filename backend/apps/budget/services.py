"""Servicios del ciclo presupuestario SIS-POA (Fase 1: gestión fiscal).

Implementan los bloqueos por gestión (§10 del prompt maestro): las fases 2+
validan el estado de la gestión a través de estas funciones antes de operar
(techo directivo, distribución, fijación, reformulaciones…).

Estados del ciclo usados (nuevos códigos de `GestionFiscal.Estado`):
    CONFIGURACION → HABILITADA → EN_FORMULACION → VIGENTE → CERRADA
Los estados legacy se reconocen en los helpers para no romper la UI V1
(mapeo: preparacion≈CONFIGURACION, abierta≈HABILITADA,
formulacion≈EN_FORMULACION, cerrada≈CERRADA).
"""
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from apps.auditoria.models import EventoAuditoria
from apps.auditoria.services import registrar_evento
from apps.gestion.models import CicloFormulacion, EtapaFormulacion, GestionFiscal

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
