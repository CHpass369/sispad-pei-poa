from django.db import models
from typing import Optional


def select_proyectos_inversion(prioridad: Optional[int] = None, etapa: Optional[str] = None, ue_id=None, fuente_id=None, activo: Optional[bool] = None, search: Optional[str] = None, gestion_inicio: Optional[int] = None):
    """Queryset for listing proyectos de inversion."""
    from .models import ProyectoInversion
    qs = ProyectoInversion.objects.select_related('tipo', 'ue', 'programa', 'fuente', 'organismo')
    if prioridad is not None:
        qs = qs.filter(prioridad=prioridad)
    if etapa:
        qs = qs.filter(etapa=etapa)
    if ue_id:
        qs = qs.filter(ue_id=ue_id)
    if fuente_id:
        qs = qs.filter(fuente_id=fuente_id)
    if activo is not None:
        qs = qs.filter(activo=activo)
    if search:
        qs = qs.filter(models.Q(nombre__icontains=search) | models.Q(codigo_interno__icontains=search) | models.Q(codigo_sisin__icontains=search))
    if gestion_inicio:
        qs = qs.filter(gestion_inicio__lte=gestion_inicio)
    return qs


def select_proyecto_inversion_by_id(proyecto_id):
    """Get single ProyectoInversion by UUID."""
    from .models import ProyectoInversion
    return ProyectoInversion.objects.filter(pk=proyecto_id).first()


def select_programaciones_plurianuales(proyecto_id=None, anio: Optional[int] = None):
    """Queryset for listing programaciones plurianuales de proyectos."""
    from .models import ProgramacionPlurianualProyecto
    qs = ProgramacionPlurianualProyecto.objects.select_related('proyecto')
    if proyecto_id:
        qs = qs.filter(proyecto_id=proyecto_id)
    if anio:
        qs = qs.filter(anio=anio)
    return qs


def select_programacion_plurianual_by_id(programacion_id):
    """Get single ProgramacionPlurianualProyecto by UUID."""
    from .models import ProgramacionPlurianualProyecto
    return ProgramacionPlurianualProyecto.objects.filter(pk=programacion_id).first()


def select_programaciones_fisicas_financieras(proyecto_id=None, gestion: Optional[int] = None):
    """Queryset for listing programaciones fisicas y financieras."""
    from .models import ProgramacionFisicaFinanciera
    qs = ProgramacionFisicaFinanciera.objects.select_related('proyecto')
    if proyecto_id:
        qs = qs.filter(proyecto_id=proyecto_id)
    if gestion:
        qs = qs.filter(gestion=gestion)
    return qs


def select_programacion_fisica_financiera_by_id(programacion_id):
    """Get single ProgramacionFisicaFinanciera by UUID."""
    from .models import ProgramacionFisicaFinanciera
    return ProgramacionFisicaFinanciera.objects.filter(pk=programacion_id).first()
