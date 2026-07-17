from decimal import Decimal


def validar_porcentaje_rango(porcentaje):
    if porcentaje is None:
        return {'valido': False, 'mensaje': 'El porcentaje es requerido.'}
    porcentaje = Decimal(str(porcentaje))
    if porcentaje < Decimal('0') or porcentaje > Decimal('100'):
        return {
            'valido': False,
            'mensaje': 'El porcentaje (' + str(porcentaje) + '%) debe estar entre 0 y 100.',
        }
    return {'valido': True, 'mensaje': 'Porcentaje en rango valido.'}


def validar_evidencia_requerida(entrada):
    if entrada.porcentaje_avance_fisico and entrada.porcentaje_avance_fisico > 0:
        if not entrada.evidencia or not entrada.evidencia.strip():
            return {
                'valido': False,
                'mensaje': 'La evidencia es requerida cuando hay avance fisico.',
            }
    return {'valido': True, 'mensaje': 'Evidencia validada.'}


def validar_fecha_seguimiento(reporte, periodo):
    if reporte.gestion is None:
        return {'valido': False, 'mensaje': 'La gestion del reporte es requerida.'}
    if not periodo or not periodo.strip():
        return {'valido': False, 'mensaje': 'El periodo es requerido.'}
    from apps.seguimiento.models import ReporteSeguimiento
    duplicado = ReporteSeguimiento.objects.filter(
        gestion=reporte.gestion,
        periodo=periodo,
        unidad_organizacional=reporte.unidad_organizacional,
    )
    if reporte.pk:
        duplicado = duplicado.exclude(pk=reporte.pk)
    if duplicado.exists():
        return {
            'valido': False,
            'mensaje': (
                'Ya existe un reporte para la gestion ' + str(reporte.gestion)
                + ', periodo "' + periodo + '" en esta unidad.'
            ),
        }
    return {'valido': True, 'mensaje': 'Fecha de seguimiento valida.'}
