from django.db import models
from typing import Optional


def select_poaus(gestion: Optional[int] = None, unidad_id=None, estado: Optional[str] = None, responsable_id=None, search: Optional[str] = None):
    """Queryset for listing POAUs."""
    from .models import POAU
    qs = POAU.objects.select_related('unidad', 'producto_territorial', 'responsable')
    if gestion:
        qs = qs.filter(gestion=gestion)
    if unidad_id:
        qs = qs.filter(unidad_id=unidad_id)
    if estado:
        qs = qs.filter(estado=estado)
    if responsable_id:
        qs = qs.filter(responsable_id=responsable_id)
    if search:
        qs = qs.filter(models.Q(nombre__icontains=search) | models.Q(codigo__icontains=search))
    return qs


def select_poau_by_id(poau_id):
    """Get single POAU by PK."""
    from .models import POAU
    return POAU.objects.filter(pk=poau_id).first()


def select_poau_by_codigo(codigo: str):
    """Get single POAU by codigo."""
    from .models import POAU
    return POAU.objects.filter(codigo=codigo).first()


def select_actividades_poau(poau_id=None, search: Optional[str] = None):
    """Queryset for listing actividades del POAU."""
    from .models import POAUActividad
    qs = POAUActividad.objects.select_related('poau', 'objeto_gasto', 'accion_corto_plazo')
    if poau_id:
        qs = qs.filter(poau_id=poau_id)
    if search:
        qs = qs.filter(models.Q(nombre__icontains=search) | models.Q(codigo__icontains=search))
    return qs


def select_actividad_poau_by_id(actividad_id):
    """Get single POAUActividad by PK."""
    from .models import POAUActividad
    return POAUActividad.objects.filter(pk=actividad_id).first()


def select_ejecuciones_fisicas(actividad_id=None, periodo: Optional[str] = None, tipo_periodo: Optional[str] = None):
    """Queryset for listing ejecuciones fisicas."""
    from .models import EjecucionFisica
    qs = EjecucionFisica.objects.select_related('actividad')
    if actividad_id:
        qs = qs.filter(actividad_id=actividad_id)
    if periodo:
        qs = qs.filter(periodo=periodo)
    if tipo_periodo:
        qs = qs.filter(tipo_periodo=tipo_periodo)
    return qs


def select_ejecucion_fisica_by_id(ejecucion_id):
    """Get single EjecucionFisica by PK."""
    from .models import EjecucionFisica
    return EjecucionFisica.objects.filter(pk=ejecucion_id).first()


def select_ejecuciones_financieras(actividad_id=None, periodo: Optional[str] = None, tipo_periodo: Optional[str] = None):
    """Queryset for listing ejecuciones financieras."""
    from .models import EjecucionFinanciera
    qs = EjecucionFinanciera.objects.select_related('actividad')
    if actividad_id:
        qs = qs.filter(actividad_id=actividad_id)
    if periodo:
        qs = qs.filter(periodo=periodo)
    if tipo_periodo:
        qs = qs.filter(tipo_periodo=tipo_periodo)
    return qs


def select_ejecucion_financiera_by_id(ejecucion_id):
    """Get single EjecucionFinanciera by PK."""
    from .models import EjecucionFinanciera
    return EjecucionFinanciera.objects.filter(pk=ejecucion_id).first()
