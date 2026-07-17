from django.db import models
from typing import Optional


def select_programas_presupuestarios(gestion: Optional[int] = None, ue_id=None, activo: Optional[bool] = None, search: Optional[str] = None):
    """Queryset for listing programas presupuestarios."""
    from .models import ProgramaPresupuestario
    qs = ProgramaPresupuestario.objects.select_related('ue_responsable')
    if gestion:
        qs = qs.filter(gestion=gestion)
    if ue_id:
        qs = qs.filter(ue_responsable_id=ue_id)
    if activo is not None:
        qs = qs.filter(activo=activo)
    if search:
        qs = qs.filter(models.Q(nombre__icontains=search) | models.Q(codigo__icontains=search))
    return qs


def select_programa_by_id(programa_id):
    """Get single ProgramaPresupuestario by UUID."""
    from .models import ProgramaPresupuestario
    return ProgramaPresupuestario.objects.filter(pk=programa_id).first()


def select_proyectos_presupuestarios(programa_id=None, gestion: Optional[int] = None, activo: Optional[bool] = None, search: Optional[str] = None):
    """Queryset for listing proyectos presupuestarios."""
    from .models import ProyectoPresupuestario
    qs = ProyectoPresupuestario.objects.select_related('programa')
    if programa_id:
        qs = qs.filter(programa_id=programa_id)
    if gestion:
        qs = qs.filter(gestion=gestion)
    if activo is not None:
        qs = qs.filter(activo=activo)
    if search:
        qs = qs.filter(models.Q(nombre__icontains=search) | models.Q(codigo__icontains=search))
    return qs


def select_proyecto_by_id(proyecto_id):
    """Get single ProyectoPresupuestario by UUID."""
    from .models import ProyectoPresupuestario
    return ProyectoPresupuestario.objects.filter(pk=proyecto_id).first()


def select_actividades_presupuestarias(proyecto_id=None, gestion: Optional[int] = None, activo: Optional[bool] = None, search: Optional[str] = None):
    """Queryset for listing actividades presupuestarias."""
    from .models import ActividadPresupuestaria
    qs = ActividadPresupuestaria.objects.select_related('proyecto')
    if proyecto_id:
        qs = qs.filter(proyecto_id=proyecto_id)
    if gestion:
        qs = qs.filter(gestion=gestion)
    if activo is not None:
        qs = qs.filter(activo=activo)
    if search:
        qs = qs.filter(models.Q(nombre__icontains=search) | models.Q(codigo__icontains=search))
    return qs


def select_actividad_by_id(actividad_id):
    """Get single ActividadPresupuestaria by UUID."""
    from .models import ActividadPresupuestaria
    return ActividadPresupuestaria.objects.filter(pk=actividad_id).first()


def select_lineas_presupuestarias(gestion: Optional[int] = None, programa_id=None, ue_id=None, fuente_id=None, objeto_gasto_id=None, activo: Optional[bool] = None, version: Optional[int] = None):
    """Queryset for listing lineas presupuestarias."""
    from .models import LineaPresupuestaria
    qs = LineaPresupuestaria.objects.select_related(
        'da', 'ue', 'programa', 'proyecto', 'actividad',
        'finalidad_funcion', 'fuente', 'organismo', 'objeto_gasto',
        'entidad_transferencia', 'operacion'
    )
    if gestion:
        qs = qs.filter(gestion=gestion)
    if programa_id:
        qs = qs.filter(programa_id=programa_id)
    if ue_id:
        qs = qs.filter(ue_id=ue_id)
    if fuente_id:
        qs = qs.filter(fuente_id=fuente_id)
    if objeto_gasto_id:
        qs = qs.filter(objeto_gasto_id=objeto_gasto_id)
    if activo is not None:
        qs = qs.filter(activo=activo)
    if version is not None:
        qs = qs.filter(version=version)
    return qs


def select_linea_by_id(linea_id):
    """Get single LineaPresupuestaria by UUID."""
    from .models import LineaPresupuestaria
    return LineaPresupuestaria.objects.filter(pk=linea_id).first()
