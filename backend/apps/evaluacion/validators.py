def validar_criterios_completos(evaluacion):
    from apps.evaluacion.models import CriterioEvaluacion
    criterios_esperados = ['eficacia', 'eficiencia', 'efectividad', 'pertinencia', 'impacto', 'sostenibilidad']
    existentes = set(
        CriterioEvaluacion.objects.filter(
            evaluacion=evaluacion
        ).values_list('criterion', flat=True)
    )
    faltantes = [c for c in criterios_esperados if c not in existentes]
    if faltantes:
        return {
            'valido': False,
            'mensaje': 'Faltan criterios de evaluacion: ' + ', '.join(faltantes),
        }
    return {'valido': True, 'mensaje': 'Todos los criterios estan presentes.'}


def validar_score_rango(score):
    from decimal import Decimal
    if score is None:
        return {'valido': False, 'mensaje': 'El puntaje es requerido.'}
    score = Decimal(str(score))
    if score < Decimal('0') or score > Decimal('100'):
        return {
            'valido': False,
            'mensaje': 'El puntaje (' + str(score) + ') debe estar entre 0 y 100.',
        }
    return {'valido': True, 'mensaje': 'Puntaje en rango valido.'}


def validar_evaluacion_periodo(evaluacion):
    if evaluacion.fiscal_year is None:
        return {'valido': False, 'mensaje': 'La gestion es requerida.'}
    if evaluacion.evaluation_type is None:
        return {'valido': False, 'mensaje': 'El tipo de evaluacion es requerido.'}
    if evaluacion.period is None:
        return {'valido': False, 'mensaje': 'El periodo es requerido.'}
    from apps.evaluacion.models import Evaluacion
    duplicada = Evaluacion.objects.filter(
        plan=evaluacion.plan,
        fiscal_year=evaluacion.fiscal_year,
        evaluation_type=evaluacion.evaluation_type,
        period=evaluacion.period,
    )
    if evaluacion.pk:
        duplicada = duplicada.exclude(pk=evaluacion.pk)
    if duplicada.exists():
        return {
            'valido': False,
            'mensaje': 'Ya existe una evaluacion igual para este plan, gestion, tipo y periodo.',
        }
    return {'valido': True, 'mensaje': 'Periodo de evaluacion valido.'}
