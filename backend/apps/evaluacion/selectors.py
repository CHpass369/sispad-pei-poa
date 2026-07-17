from django.db import models
from typing import Optional


def select_evaluaciones(plan_id=None, fiscal_year: Optional[int] = None, evaluation_type: Optional[str] = None, period: Optional[str] = None, status: Optional[str] = None):
    """Queryset for listing evaluaciones."""
    from .models import Evaluacion
    qs = Evaluacion.objects.select_related('plan')
    if plan_id:
        qs = qs.filter(plan_id=plan_id)
    if fiscal_year:
        qs = qs.filter(fiscal_year=fiscal_year)
    if evaluation_type:
        qs = qs.filter(evaluation_type=evaluation_type)
    if period:
        qs = qs.filter(period=period)
    if status:
        qs = qs.filter(status=status)
    return qs


def select_evaluacion_by_id(evaluacion_id):
    """Get single Evaluacion by UUID."""
    from .models import Evaluacion
    return Evaluacion.objects.filter(pk=evaluacion_id).first()


def select_criterios_evaluacion(evaluacion_id=None, criterion: Optional[str] = None):
    """Queryset for listing criterios de evaluacion."""
    from .models import CriterioEvaluacion
    qs = CriterioEvaluacion.objects.select_related('evaluacion')
    if evaluacion_id:
        qs = qs.filter(evaluacion_id=evaluacion_id)
    if criterion:
        qs = qs.filter(criterion=criterion)
    return qs


def select_criterio_by_id(criterio_id):
    """Get single CriterioEvaluacion by UUID."""
    from .models import CriterioEvaluacion
    return CriterioEvaluacion.objects.filter(pk=criterio_id).first()


def select_resultados_evaluacion(evaluacion_id=None, status: Optional[str] = None, poau_id=None, unidad_id=None):
    """Queryset for listing resultados de evaluacion."""
    from .models import ResultadoEvaluacion
    qs = ResultadoEvaluacion.objects.select_related('evaluacion', 'poau', 'unidad', 'resultado_pad')
    if evaluacion_id:
        qs = qs.filter(evaluacion_id=evaluacion_id)
    if status:
        qs = qs.filter(status=status)
    if poau_id:
        qs = qs.filter(poau_id=poau_id)
    if unidad_id:
        qs = qs.filter(unidad_id=unidad_id)
    return qs


def select_resultado_evaluacion_by_id(resultado_id):
    """Get single ResultadoEvaluacion by UUID."""
    from .models import ResultadoEvaluacion
    return ResultadoEvaluacion.objects.filter(pk=resultado_id).first()


def select_lecciones_aprendidas(evaluacion_id=None, category: Optional[str] = None, search: Optional[str] = None):
    """Queryset for listing lecciones aprendidas."""
    from .models import LeccionAprendida
    qs = LeccionAprendida.objects.select_related('evaluacion')
    if evaluacion_id:
        qs = qs.filter(evaluacion_id=evaluacion_id)
    if category:
        qs = qs.filter(category=category)
    if search:
        qs = qs.filter(models.Q(title__icontains=search) | models.Q(description__icontains=search))
    return qs


def select_leccion_by_id(leccion_id):
    """Get single LeccionAprendida by UUID."""
    from .models import LeccionAprendida
    return LeccionAprendida.objects.filter(pk=leccion_id).first()


def select_recomendaciones(evaluacion_id=None, priority: Optional[str] = None, status: Optional[str] = None, search: Optional[str] = None):
    """Queryset for listing recomendaciones."""
    from .models import Recomendacion
    qs = Recomendacion.objects.select_related('evaluacion')
    if evaluacion_id:
        qs = qs.filter(evaluacion_id=evaluacion_id)
    if priority:
        qs = qs.filter(priority=priority)
    if status:
        qs = qs.filter(status=status)
    if search:
        qs = qs.filter(description__icontains=search)
    return qs


def select_recomendacion_by_id(recomendacion_id):
    """Get single Recomendacion by UUID."""
    from .models import Recomendacion
    return Recomendacion.objects.filter(pk=recomendacion_id).first()
