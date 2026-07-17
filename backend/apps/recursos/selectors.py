from django.db import models
from typing import Optional


def select_estimaciones_recurso(gestion: Optional[int] = None, rubro_id=None, fuente_id=None, activo: Optional[bool] = None, version: Optional[int] = None):
    """Queryset for listing estimaciones de recurso."""
    from .models import EstimacionRecurso
    qs = EstimacionRecurso.objects.select_related('rubro', 'fuente', 'organismo')
    if gestion:
        qs = qs.filter(gestion=gestion)
    if rubro_id:
        qs = qs.filter(rubro_id=rubro_id)
    if fuente_id:
        qs = qs.filter(fuente_id=fuente_id)
    if activo is not None:
        qs = qs.filter(activo=activo)
    if version is not None:
        qs = qs.filter(version=version)
    return qs


def select_estimacion_recurso_by_id(estimacion_id):
    """Get single EstimacionRecurso by UUID."""
    from .models import EstimacionRecurso
    return EstimacionRecurso.objects.filter(pk=estimacion_id).first()


def select_estimaciones_plurianuales(estimacion_origen_id=None, anio: Optional[int] = None):
    """Queryset for listing estimaciones plurianuales."""
    from .models import EstimacionPlurianual
    qs = EstimacionPlurianual.objects.select_related('estimacion_origen')
    if estimacion_origen_id:
        qs = qs.filter(estimacion_origen_id=estimacion_origen_id)
    if anio:
        qs = qs.filter(anio=anio)
    return qs


def select_estimacion_plurianual_by_id(plurianual_id):
    """Get single EstimacionPlurianual by UUID."""
    from .models import EstimacionPlurianual
    return EstimacionPlurianual.objects.filter(pk=plurianual_id).first()
