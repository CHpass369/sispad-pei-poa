from django.db import transaction
from django.utils import timezone

from .models import GestionFiscal, CicloFormulacion, EtapaFormulacion

import logging

logger = logging.getLogger(__name__)


def estado_operativo(estado):
    """Mapeo centralizado 10→4 de estados de gestión (Q3, design §10).

    BORRADOR ← preparacion/abierta/formulacion/revision/consolidacion
    VIGENTE  ← aprobacion/vigente
    CERRADA  ← cerrada/archivada
    ANULADA  ← anulada

    Único lugar que define el estado operativo; lo usan el wizard, la
    API y la validación del núcleo de techos. El núcleo NO inventa un
    ciclo paralelo: GestionFiscal sigue siendo la fuente (R1.1).
    """
    if estado in (
        GestionFiscal.Estado.PREPARACION,
        GestionFiscal.Estado.ABIERTA,
        GestionFiscal.Estado.FORMULACION,
        GestionFiscal.Estado.REVISION,
        GestionFiscal.Estado.CONSOLIDACION,
    ):
        return 'BORRADOR'
    if estado in (GestionFiscal.Estado.APROBACION, GestionFiscal.Estado.VIGENTE):
        return 'VIGENTE'
    if estado in (GestionFiscal.Estado.CERRADA, GestionFiscal.Estado.ARCHIVADA):
        return 'CERRADA'
    if estado == GestionFiscal.Estado.ANULADA:
        return 'ANULADA'
    # Fallback silencioso a BORRADOR (sospechoso 4R): no inventar un
    # mapeo; loguear para que un estado nuevo sin mapear no pase
    # desapercibido (p. ej. un valor que ya no existe en choices o un
    # estado aditivo agregado en el futuro).
    logger.warning(
        'estado_operativo: estado %r sin mapeo explícito; se asume '
        'BORRADOR (Q3). Revisar GestionFiscal.Estado.',
        estado,
    )
    return 'BORRADOR'


def crear_gestion(anio, descripcion='', anio_inicio_plurianual=None, anio_fin_plurianual=None, creado_por=None):
    gestion = GestionFiscal(
        anio=anio,
        descripcion=descripcion,
        anio_inicio_plurianual=anio_inicio_plurianual,
        anio_fin_plurianual=anio_fin_plurianual,
        estado=GestionFiscal.Estado.PREPARACION,
        creado_por=creado_por,
    )
    gestion.save()
    return gestion


def obtener_gestion_actual():
    return GestionFiscal.objects.filter(activa=True).order_by('-anio').first()


def obtener_gestion_por_anio(anio):
    try:
        return GestionFiscal.objects.get(anio=anio)
    except GestionFiscal.DoesNotExist:
        return None


@transaction.atomic
def cerrar_gestion(gestion):
    estados_finales = (GestionFiscal.Estado.CERRADA, GestionFiscal.Estado.ARCHIVADA)
    if gestion.estado in estados_finales:
        return {
            'exito': False,
            'mensaje': f'La gestión {gestion.anio} ya se encuentra en estado {gestion.get_estado_display()}.',
        }
    gestion.estado = GestionFiscal.Estado.CERRADA
    gestion.fecha_cierre = timezone.now()
    gestion.activa = False
    gestion.save(update_fields=['estado', 'fecha_cierre', 'activa', 'actualizado_en'])
    return {
        'exito': True,
        'mensaje': f'Gestión {gestion.anio} cerrada exitosamente.',
    }


def validar_fechas_gestion(gestion):
    errores = []
    if gestion.anio_fin_plurianual and gestion.anio_inicio_plurianual:
        if gestion.anio_fin_plurianual <= gestion.anio_inicio_plurianual:
            errores.append('El año final debe ser posterior al año inicial del plurianual.')
        if gestion.anio < gestion.anio_inicio_plurianual or gestion.anio > gestion.anio_fin_plurianual:
            errores.append('El año de gestión debe estar dentro del horizonte plurianual.')
    if gestion.fecha_apertura and gestion.fecha_cierre:
        if gestion.fecha_cierre <= gestion.fecha_apertura:
            errores.append('La fecha de cierre debe ser posterior a la de apertura.')
    return {'valido': len(errores) == 0, 'errores': errores}


def avanzar_estado_gestion(gestion, nuevo_estado):
    transiciones_validas = {
        GestionFiscal.Estado.PREPARACION: [GestionFiscal.Estado.ABIERTA],
        GestionFiscal.Estado.ABIERTA: [GestionFiscal.Estado.FORMULACION],
        GestionFiscal.Estado.FORMULACION: [GestionFiscal.Estado.REVISION],
        GestionFiscal.Estado.REVISION: [
            GestionFiscal.Estado.CONSOLIDACION,
            GestionFiscal.Estado.FORMULACION,
        ],
        GestionFiscal.Estado.CONSOLIDACION: [GestionFiscal.Estado.APROBACION],
        GestionFiscal.Estado.APROBACION: [GestionFiscal.Estado.CERRADA],
        GestionFiscal.Estado.CERRADA: [GestionFiscal.Estado.ARCHIVADA],
    }
    permitidos = transiciones_validas.get(gestion.estado, [])
    if nuevo_estado not in permitidos:
        return {
            'exito': False,
            'mensaje': (
                f'No se puede transitar de "{gestion.get_estado_display()}" '
                f'a "{dict(GestionFiscal.Estado.choices).get(nuevo_estado, nuevo_estado)}". '
                f'Estados válidos: {[dict(GestionFiscal.Estado.choices).get(e, e) for e in permitidos]}'
            ),
        }
    gestion.estado = nuevo_estado
    gestion.save(update_fields=['estado', 'actualizado_en'])
    return {'exito': True, 'mensaje': 'Estado actualizado.'}


def crear_ciclo_formulacion(gestion, nombre, fecha_inicio, fecha_cierre, descripcion=''):
    ciclo = CicloFormulacion.objects.create(
        gestion=gestion,
        nombre=nombre,
        fecha_inicio=fecha_inicio,
        fecha_cierre=fecha_cierre,
        descripcion=descripcion,
    )
    return ciclo


def crear_etapa_formulacion(ciclo, codigo, nombre, fecha_inicio, fecha_cierre, orden=0):
    etapa = EtapaFormulacion.objects.create(
        ciclo=ciclo,
        codigo=codigo,
        nombre=nombre,
        fecha_inicio=fecha_inicio,
        fecha_cierre=fecha_cierre,
        orden=orden,
    )
    return etapa


def obtener_ciclos_por_gestion(gestion):
    return CicloFormulacion.objects.filter(
        gestion=gestion, activo=True
    ).prefetch_related('etapas').order_by('orden')


def obtener_etapas_ciclo(ciclo):
    return EtapaFormulacion.objects.filter(ciclo=ciclo).order_by('orden')
