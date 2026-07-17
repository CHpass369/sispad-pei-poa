from decimal import Decimal
from django.db.models import Sum, Count, Q, F, Avg, DecimalField
from django.db.models.functions import Coalesce

from .models import (
    Evaluacion, CriterioEvaluacion, ResultadoEvaluacion,
    LeccionAprendida,
)
from apps.poau.models import POAU, POAUActividad, EjecucionFisica, EjecucionFinanciera
from apps.organizacion.models import UnidadOrganizacional
from apps.pad.models import ResultadoTerritorial


CRITERIOS_POR_DEFECTO = [
    ('eficacia', Decimal('0.20'), 'Grado de cumplimiento de objetivos y metas programadas.'),
    ('eficiencia', Decimal('0.15'), 'Relación entre los recursos utilizados y los resultados obtenidos.'),
    ('efectividad', Decimal('0.20'), 'Capacidad de generar los efectos deseados en el territorio.'),
    ('pertinencia', Decimal('0.15'), 'Grado de adecuación de las acciones a las necesidades reales.'),
    ('impacto', Decimal('0.15'), 'Alcance de los cambios generados en la población beneficiaria.'),
    ('sostenibilidad', Decimal('0.15'), 'Capacidad de mantener los resultados a largo plazo.'),
]


def generar_evaluacion(gestion, tipo, plan_id=None, periodo='AN'):
    """Genera una evaluación completa con criterios predefinidos.

    Crea la evaluación, los 6 criterios con pesos por defecto, y ejecuta
    la evaluación por POAU, unidad y resultado PAD.

    Returns:
        Evaluacion: la evaluación creada con todos los datos poblados.
    """
    from apps.planificacion.models import Plan

    if plan_id:
        plan = Plan.objects.get(id=plan_id)
    else:
        plan = Plan.objects.filter(tipo='pei').order_by('-gestion_inicio').first()
        if not plan:
            plan = Plan.objects.order_by('-gestion_inicio').first()
        if not plan:
            raise ValueError('No existe ningún plan registrado en el sistema.')

    evaluacion, created = Evaluacion.objects.get_or_create(
        plan=plan,
        fiscal_year=gestion,
        evaluation_type=tipo,
        period=periodo,
        defaults={
            'status': 'borrador',
            'responsible_team': 'Equipo de Evaluación Institucional',
        },
    )

    if created:
        for criterio_code, peso, justificacion in CRITERIOS_POR_DEFECTO:
            CriterioEvaluacion.objects.create(
                evaluacion=evaluacion,
                criterion=criterio_code,
                weight=peso,
                justification=justificacion,
            )

        evaluar_por_poau(evaluacion)
        evaluar_por_unidad(evaluacion)
        evaluar_por_resultado_pad(evaluacion)
        evaluar_institucional(evaluacion)

        score = calcular_score_global(evaluacion)
        evaluacion.status = 'en_curso'
        evaluacion.save(update_fields=['status', 'updated_at'])

    return evaluacion


def calcular_score_global(evaluacion):
    """Calcula el puntaje global ponderado de una evaluación.

    Multiplica cada criterio por su peso y suma los resultados.
    Actualiza también los resultados asociados.

    Returns:
        Decimal: puntaje global ponderado.
    """
    criterios = evaluacion.criterios.all()
    if not criterios.exists():
        return Decimal('0.00')

    score_total = Decimal('0.00')
    peso_total = Decimal('0.00')

    for criterio in criterios:
        score_total += criterio.score * criterio.weight
        peso_total += criterio.weight

    if peso_total > 0:
        score_global = (score_total / peso_total).quantize(Decimal('0.01'))
    else:
        score_global = Decimal('0.00')

    resultados = evaluacion.resultados.all()
    for resultado in resultados:
        _recalcular_score_resultado(resultado)

    return score_global


def _recalcular_score_resultado(resultado):
    """Recalcula el puntaje y estado de un resultado individual."""
    evaluacion = resultado.evaluacion
    criterios = evaluacion.criterios.all()

    if not criterios.exists():
        return

    score_base = Decimal('0.00')
    peso_total = Decimal('0.00')

    for criterio in criterios:
        score_base += criterio.score * criterio.weight
        peso_total += criterio.weight

    if peso_total > 0:
        score = (score_base / peso_total).quantize(Decimal('0.01'))
    else:
        score = Decimal('0.00')

    resultado.score_global = score

    if score >= Decimal('75.00'):
        resultado.status = 'cumple'
    elif score >= Decimal('50.00'):
        resultado.status = 'parcial'
    else:
        resultado.status = 'no_cumple'

    resultado.save(update_fields=['score_global', 'status', 'updated_at'])


def evaluar_por_poau(evaluacion):
    """Evalúa cada POAU de la gestión.

    Calcula el avance físico-financiero de cada POAU y crea un
    ResultadoEvaluacion por cada uno.

    Returns:
        list[ResultadoEvaluacion]: resultados creados.
    """
    poaus = POAU.objects.filter(
        gestion=evaluacion.fiscal_year,
    ).select_related('unidad', 'producto_territorial')

    resultados = []

    for poau in poaus:
        actividades = poau.actividades.all()
        total_programado_fisico = Decimal('0')
        total_ejecutado_fisico = Decimal('0')
        total_programado_financiero = Decimal('0')
        total_ejecutado_financiero = Decimal('0')

        for actividad in actividades:
            ef_fisicas = EjecucionFisica.objects.filter(actividad=actividad)
            for ef in ef_fisicas:
                total_programado_fisico += ef.programado or Decimal('0')
                total_ejecutado_fisico += ef.ejecutado or Decimal('0')

            ef_financieras = EjecucionFinanciera.objects.filter(actividad=actividad)
            for ef in ef_financieras:
                total_programado_financiero += ef.programado or Decimal('0')
                total_ejecutado_financiero += ef.ejecutado or Decimal('0')

        if total_programado_fisico > 0:
            avance_fisico = (total_ejecutado_fisico / total_programado_fisico * 100).quantize(
                Decimal('0.01')
            )
        else:
            avance_fisico = Decimal('0.00')

        if total_programado_financiero > 0:
            avance_financiero = (
                total_ejecutado_financiero / total_programado_financiero * 100
            ).quantize(Decimal('0.01'))
        else:
            avance_financiero = Decimal('0.00')

        score = ((avance_fisico + avance_financiero) / 2).quantize(Decimal('0.01'))

        if score >= Decimal('75.00'):
            estado = 'cumple'
        elif score >= Decimal('50.00'):
            estado = 'parcial'
        else:
            estado = 'no_cumple'

        resultado = ResultadoEvaluacion.objects.create(
            evaluacion=evaluacion,
            poau=poau,
            unidad=poau.unidad,
            score_global=score,
            status=estado,
            observations=(
                f'Avance físico: {avance_fisico}%, '
                f'Avance financiero: {avance_financiero}%'
            ),
        )
        resultados.append(resultado)

    return resultados


def evaluar_por_unidad(evaluacion):
    """Evalúa cada unidad organizacional que tiene POAUs en la gestión.

    Agrega los puntajes de todos los POAUs de cada unidad y crea un
    ResultadoEvaluacion consolidado por unidad.

    Returns:
        list[ResultadoEvaluacion]: resultados creados.
    """
    unidades_con_poau = (
        POAU.objects.filter(gestion=evaluacion.fiscal_year)
        .values('unidad_id')
        .annotate(
            total_poau=Count('id'),
            promedio_score=Coalesce(
                Sum('resultados_evaluacion__score_global'), Decimal('0'),
                output_field=DecimalField(max_digits=10, decimal_places=2),
            ),
        )
    )

    resultados = []

    for item in unidades_con_poau:
        unidad_id = item['unidad_id']
        if not unidad_id:
            continue

        try:
            unidad = UnidadOrganizacional.objects.get(id=unidad_id)
        except UnidadOrganizacional.DoesNotExist:
            continue

        existing = ResultadoEvaluacion.objects.filter(
            evaluacion=evaluacion,
            unidad=unidad,
            poau__isnull=True,
            resultado_pad__isnull=True,
        ).first()

        total_poau = item['total_poau']
        if total_poau > 0:
            score = (item['promedio_score'] / total_poau).quantize(Decimal('0.01'))
        else:
            score = Decimal('0.00')

        if score >= Decimal('75.00'):
            estado = 'cumple'
        elif score >= Decimal('50.00'):
            estado = 'parcial'
        else:
            estado = 'no_cumple'

        if existing:
            existing.score_global = score
            existing.status = estado
            existing.observations = (
                f'Consolidado de {total_poau} POAU(s). '
                f'Promedio de puntajes: {item["promedio_score"]}'
            )
            existing.save(update_fields=['score_global', 'status', 'observations', 'updated_at'])
            resultados.append(existing)
        else:
            resultado = ResultadoEvaluacion.objects.create(
                evaluacion=evaluacion,
                unidad=unidad,
                score_global=score,
                status=estado,
                observations=(
                    f'Consolidado de {total_poau} POAU(s). '
                    f'Promedio de puntajes: {item["promedio_score"]}'
                ),
            )
            resultados.append(resultado)

    return resultados


def evaluar_por_resultado_pad(evaluacion):
    """Evalúa cada resultado territorial del PAD关联ado a la gestión.

    Analiza los productos territoriales vinculados y su programación anual
    para determinar el nivel de cumplimiento.

    Returns:
        list[ResultadoEvaluacion]: resultados creados.
    """
    resultados_pad = ResultadoTerritorial.objects.filter(
        gestion=evaluacion.fiscal_year,
    ).select_related('lineamiento', 'sector')

    resultados = []

    for resultado_territorial in resultados_pad:
        programaciones = resultado_territorial.programaciones.filter(
            anio=evaluacion.fiscal_year, tipo='fisica',
        )

        if programaciones.exists():
            total_programado = programaciones.aggregate(
                t=Coalesce(Sum('valor'), Decimal('0'))
            )['t']
        else:
            total_programado = Decimal('0')

        productos = resultado_territorial.productos.all()
        total_productos = productos.count()
        productos_con_financiamiento = productos.filter(
            cuenta_con_financiamiento='SI'
        ).count()

        if total_productos > 0:
            ratio_financiamiento = (
                Decimal(str(productos_con_financiamiento)) / Decimal(str(total_productos)) * 100
            ).quantize(Decimal('0.01'))
        else:
            ratio_financiamiento = Decimal('0.00')

        if total_programado > 0:
            score = ratio_financiamiento
        else:
            score = Decimal('0.00')

        if score >= Decimal('75.00'):
            estado = 'cumple'
        elif score >= Decimal('50.00'):
            estado = 'parcial'
        else:
            estado = 'no_cumple'

        resultado = ResultadoEvaluacion.objects.create(
            evaluacion=evaluacion,
            resultado_pad=resultado_territorial,
            score_global=score,
            status=estado,
            observations=(
                f'Total productos: {total_productos}, '
                f'Con financiamiento: {productos_con_financiamiento}, '
                f'Programación física: {total_programado}'
            ),
        )
        resultados.append(resultado)

    return resultados


def evaluar_institucional(evaluacion):
    """Evaluación institucional consolidada.

    Agrega los resultados de POAU, unidad y resultado PAD para calcular
    un puntaje institucional global. Actualiza los criterios de evaluación
    con los promedios calculados.

    Returns:
        dict: resumen de la evaluación institucional.
    """
    todos_resultados = evaluacion.resultados.all()

    if not todos_resultados.exists():
        return {'score_institucional': Decimal('0.00'), 'total_resultados': 0}

    score_total = Decimal('0.00')
    for r in todos_resultados:
        score_total += r.score_global

    score_institucional = (score_total / Decimal(str(todos_resultados.count()))).quantize(
        Decimal('0.01')
    )

    total_cumple = todos_resultados.filter(status='cumple').count()
    total_parcial = todos_resultados.filter(status='parcial').count()
    total_no_cumple = todos_resultados.filter(status='no_cumple').count()

    criterio_eficacia = evaluacion.criterios.filter(criterion='eficacia').first()
    if criterio_eficacia:
        avg_score = todos_resultados.aggregate(
            avg=Coalesce(
                Avg('score_global'), Decimal('0'),
                output_field=DecimalField(max_digits=5, decimal_places=2),
            )
        )['avg']
        criterio_eficacia.score = avg_score
        criterio_eficacia.save(update_fields=['score', 'updated_at'])

    return {
        'score_institucional': score_institucional,
        'total_resultados': todos_resultados.count(),
        'cumple': total_cumple,
        'parcial': total_parcial,
        'no_cumple': total_no_cumple,
    }
