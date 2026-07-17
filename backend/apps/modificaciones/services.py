from decimal import Decimal
from django.db import transaction
from django.apps import apps
from django.utils import timezone

from .models import SolicitudModificacion, CambioModificacion, ImpactoModificacion


def crear_solicitud(tipo, entidad_tipo, entidad_id, datos=None):
    """
    Crea una solicitud de modificación vinculada a una entidad del sistema.

    Args:
        tipo: Tipo de modificación (choice de SolicitudModificacion.TIPO_CHOICES).
        entidad_tipo: Nombre del modelo (ContentType name) de la entidad afectada.
        entidad_id: UUID de la entidad afectada.
        datos: Diccionario con campos adicionales de la solicitud.

    Returns:
        Instancia de SolicitudModificacion creada.
    """
    datos = datos or {}
    solicitud = SolicitudModificacion(
        tipo=tipo,
        entidad_afectada_tipo=entidad_tipo,
        entidad_afectada_id=entidad_id,
        gestion_fiscal=datos.get('gestion_fiscal', timezone.now().year),
        motivo=datos.get('motivo', ''),
        informe_tecnico=datos.get('informe_tecnico', ''),
        documento_legal=datos.get('documento_legal', ''),
        estado='borrador',
    )

    poau_id = datos.get('poau')
    if poau_id:
        POAU = apps.get_model('poau', 'POAU')
        try:
            solicitud.poau = POAU.objects.get(pk=poau_id)
        except POAU.DoesNotExist:
            pass

    solicitante = datos.get('solicitado_por')
    if solicitante:
        solicitud.solicitado_por = solicitante

    solicitud.save()

    for cambio in datos.get('cambios', []):
        CambioModificacion.objects.create(
            solicitud=solicitud,
            campo=cambio.get('campo', ''),
            valor_anterior=cambio.get('valor_anterior', ''),
            valor_propuesto=cambio.get('valor_propuesto', ''),
        )

    return solicitud


def _obtener_entidad(tipo_modelo, entidad_id):
    """
    Resuelve una entidad del sistema a partir de su tipo e ID.
    Retorna la instancia o None si no existe.
    """
    try:
        modelo = apps.get_model(tipo_modelo)
    except LookupError:
        return None
    try:
        return modelo.objects.get(pk=entidad_id)
    except modelo.DoesNotExist:
        return None


def _aplicar_cambios_a_entidad(entidad, cambios):
    """
    Aplica los campos aprobados de una solicitud a la entidad afectada.
    Solo aplica campos cuyo valor_aprobado no sea None.
    """
    campos_actualizados = []
    for cambio in cambios:
        valor = cambio.valor_aprobado if cambio.valor_aprobado is not None else cambio.valor_propuesto
        if hasattr(entidad, cambio.campo):
            setattr(entidad, cambio.campo, valor)
            campos_actualizados.append(cambio.campo)
    if campos_actualizados:
        entidad.save(update_fields=campos_actualizados)
    return campos_actualizados


@transaction.atomic
def aplicar_modificacion(solicitud):
    """
    Aplica una solicitud de modificación aprobada sobre la entidad afectada.
    No sobreescribe la versión aprobada original; en su lugar, crea una nueva
    versión cuando el modelo lo soporta.

    Args:
        solicitud: Instancia de SolicitudModificacion con estado 'aprobada'.

    Returns:
        Diccionario con el resultado de la operación.
    """
    if solicitud.estado != 'aprobada':
        raise ValueError('La solicitud debe estar en estado "aprobada" para ser aplicada')

    entidad = _obtener_entidad(solicitud.entidad_afectada_tipo, solicitud.entidad_afectada_id)
    if entidad is None:
        raise ValueError(
            f'No se encontró la entidad {solicitud.entidad_afectada_tipo} '
            f'con ID {solicitud.entidad_afectada_id}'
        )

    campos_modificados = _aplicar_cambios_a_entidad(entidad, solicitud.cambios.all())

    if hasattr(entidad, 'version'):
        entidad.version = entidad.version + 1
        entidad.save(update_fields=['version'])

    solicitud.estado = 'cumplida'
    solicitud.fecha_efectiva = solicitud.fecha_efectiva or timezone.now().date()
    solicitud.save(update_fields=['estado', 'fecha_efectiva', 'updated_at'])

    return {
        'solicitud_id': str(solicitud.id),
        'entidad_tipo': solicitud.entidad_afectada_tipo,
        'entidad_id': str(solicitud.entidad_afectada_id),
        'campos_modificados': campos_modificados,
        'nueva_version': getattr(entidad, 'version', None),
        'estado': solicitud.estado,
    }


def calcular_impacto_financiero(solicitud):
    """
    Calcula el impacto financiero total de una solicitud sumando las
    diferencias entre valores anteriores y propuestos/aprobados de tipo
    numérico.

    Crea o actualiza el registro de ImpactoModificacion asociado.

    Args:
        solicitud: Instancia de SolicitudModificacion.

    Returns:
        Instancia de ImpactoModificacion con el impacto calculado.
    """
    impacto_total = Decimal('0.00')

    for cambio in solicitud.cambios.all():
        valor_original = cambio.valor_aprobado or cambio.valor_anterior
        valor_nuevo = cambio.valor_aprobado if cambio.valor_aprobado is not None else cambio.valor_propuesto

        try:
            original = Decimal(valor_original) if valor_original else Decimal('0.00')
        except (TypeError, ValueError):
            original = Decimal('0.00')

        try:
            nuevo = Decimal(valor_nuevo) if valor_nuevo else Decimal('0.00')
        except (TypeError, ValueError):
            nuevo = Decimal('0.00')

        impacto_total += nuevo - original

    impacto_absoluto = abs(impacto_total)

    impacto, _ = ImpactoModificacion.objects.update_or_create(
        solicitud=solicitud,
        defaults={
            'impacto_financiero': impacto_absoluto,
            'impacto_fisico': f'Variación de {impacto_total} en campos financieros.',
            'impacto_estrategico': (
                f'Incremento de Bs. {impacto_total:.2f} sobre el presupuesto vigente.'
                if impacto_total > 0
                else f'Reducción de Bs. {abs(impacto_total):.2f} sobre el presupuesto vigente.'
            ),
        },
    )
    return impacto


def verificar_compatibilidad(solicitud):
    """
    Verifica que una solicitud de modificación sea compatible con el estado
    actual de la entidad afectada.

    Comprueba:
    1. Que la entidad exista.
    2. Que la solicitud esté en estado que permita procesamiento.
    3. Que los campos a modificar existan en la entidad.

    Args:
        solicitud: Instancia de SolicitudModificacion.

    Returns:
        Diccionario con {compatible: bool, detalles: list[str]}.
    """
    detalles = []
    compatible = True

    entidad = _obtener_entidad(solicitud.entidad_afectada_tipo, solicitud.entidad_afectada_id)
    if entidad is None:
        compatible = False
        detalles.append(
            f'La entidad {solicitud.entidad_afectada_tipo} con ID '
            f'{solicitud.entidad_afectada_id} no existe.'
        )

    if solicitud.estado not in ('borrador', 'en_revision'):
        compatible = False
        detalles.append(
            f'La solicitud está en estado "{solicitud.get_estado_display()}", '
            f'solo se puede procesar en borrador o en revisión.'
        )

    if entidad is not None:
        for cambio in solicitud.cambios.all():
            if not hasattr(entidad, cambio.campo):
                compatible = False
                detalles.append(
                    f'El campo "{cambio.campo}" no existe en '
                    f'{solicitud.entidad_afectada_tipo}.'
                )

    if solicitud.poau is not None:
        try:
            POAU = apps.get_model('poau', 'POAU')
            poau = POAU.objects.get(pk=solicitud.poau_id)
            if poau.estado == 'aprobado':
                detalles.append(
                    'El POAU asociado está aprobado. Se creará una nueva versión '
                    'al aplicar la modificación.'
                )
        except POAU.DoesNotExist:
            compatible = False
            detalles.append(f'El POAU con ID {solicitud.poau_id} no existe.')

    if compatible and not detalles:
        detalles.append('La solicitud es compatible y puede ser procesada.')

    return {
        'compatible': compatible,
        'detalles': detalles,
    }
