from django.db import models
from typing import Optional


def select_planes(tipo: Optional[str] = None, activo: Optional[bool] = None, search: Optional[str] = None, gestion_inicio: Optional[int] = None):
    """Queryset for listing planes."""
    from .models import Plan
    qs = Plan.objects.all()
    if tipo:
        qs = qs.filter(tipo=tipo)
    if activo is not None:
        qs = qs.filter(activo=activo)
    if search:
        qs = qs.filter(models.Q(nombre__icontains=search) | models.Q(codigo__icontains=search))
    if gestion_inicio:
        qs = qs.filter(gestion_inicio__lte=gestion_inicio, gestion_fin__gte=gestion_inicio)
    return qs


def select_plan_by_id(plan_id):
    """Get single Plan by UUID."""
    from .models import Plan
    return Plan.objects.filter(pk=plan_id).first()


def select_sectores(activo: Optional[bool] = None, search: Optional[str] = None):
    """Queryset for listing sectores."""
    from .models import Sector
    qs = Sector.objects.all()
    if activo is not None:
        qs = qs.filter(activo=activo)
    if search:
        qs = qs.filter(models.Q(nombre__icontains=search) | models.Q(codigo__icontains=search))
    return qs


def select_sector_by_id(sector_id):
    """Get single Sector by UUID."""
    from .models import Sector
    return Sector.objects.filter(pk=sector_id).first()


def select_nodos_planificacion(plan_id=None, nivel: Optional[str] = None, padre_id=None, gestion: Optional[int] = None, activo: Optional[bool] = None, search: Optional[str] = None):
    """Queryset for listing nodos de planificacion."""
    from .models import NodoPlanificacion
    qs = NodoPlanificacion.objects.select_related('plan', 'padre')
    if plan_id:
        qs = qs.filter(plan_id=plan_id)
    if nivel:
        qs = qs.filter(nivel=nivel)
    if padre_id:
        qs = qs.filter(padre_id=padre_id)
    if gestion:
        qs = qs.filter(gestion=gestion)
    if activo is not None:
        qs = qs.filter(activo=activo)
    if search:
        qs = qs.filter(models.Q(nombre__icontains=search) | models.Q(codigo__icontains=search))
    return qs


def select_nodo_by_id(nodo_id):
    """Get single NodoPlanificacion by UUID."""
    from .models import NodoPlanificacion
    return NodoPlanificacion.objects.filter(pk=nodo_id).first()


def select_acciones_mediano_plazo(nodo_id=None, gestion: Optional[int] = None, activo: Optional[bool] = None, search: Optional[str] = None):
    """Queryset for listing acciones de mediano plazo."""
    from .models import AccionMedianoPlazo
    qs = AccionMedianoPlazo.objects.select_related('nodo_planificacion', 'responsable')
    if nodo_id:
        qs = qs.filter(nodo_planificacion_id=nodo_id)
    if gestion:
        qs = qs.filter(gestion_inicio__lte=gestion, gestion_fin__gte=gestion)
    if activo is not None:
        qs = qs.filter(activo=activo)
    if search:
        qs = qs.filter(models.Q(nombre__icontains=search) | models.Q(codigo__icontains=search))
    return qs


def select_accion_mediano_plazo_by_id(amp_id):
    """Get single AccionMedianoPlazo by UUID."""
    from .models import AccionMedianoPlazo
    return AccionMedianoPlazo.objects.filter(pk=amp_id).first()


def select_acciones_corto_plazo(amp_id=None, gestion: Optional[int] = None, unidad_id=None, activo: Optional[bool] = None, search: Optional[str] = None):
    """Queryset for listing acciones de corto plazo."""
    from .models import AccionCortoPlazo
    qs = AccionCortoPlazo.objects.select_related('accion_mediano_plazo', 'unidad_responsable')
    if amp_id:
        qs = qs.filter(accion_mediano_plazo_id=amp_id)
    if gestion:
        qs = qs.filter(gestion=gestion)
    if unidad_id:
        qs = qs.filter(unidad_responsable_id=unidad_id)
    if activo is not None:
        qs = qs.filter(activo=activo)
    if search:
        qs = qs.filter(models.Q(nombre__icontains=search) | models.Q(codigo__icontains=search))
    return qs


def select_accion_corto_plazo_by_id(acp_id):
    """Get single AccionCortoPlazo by UUID."""
    from .models import AccionCortoPlazo
    return AccionCortoPlazo.objects.filter(pk=acp_id).first()


def select_articulaciones(gestion: Optional[int] = None, nodo_origen_id=None, nodo_destino_id=None):
    """Queryset for listing articulaciones de planificacion."""
    from .models import ArticulacionPlanificacion
    qs = ArticulacionPlanificacion.objects.select_related('nodo_origen', 'nodo_destino')
    if gestion:
        qs = qs.filter(gestion=gestion)
    if nodo_origen_id:
        qs = qs.filter(nodo_origen_id=nodo_origen_id)
    if nodo_destino_id:
        qs = qs.filter(nodo_destino_id=nodo_destino_id)
    return qs


def select_plan_versiones(plan_id=None, status: Optional[str] = None):
    """Queryset for listing plan versions."""
    from .models import PlanVersion
    qs = PlanVersion.objects.select_related('plan', 'approved_by')
    if plan_id:
        qs = qs.filter(plan_id=plan_id)
    if status:
        qs = qs.filter(status=status)
    return qs


def select_plan_version_by_id(version_id):
    """Get single PlanVersion by UUID."""
    from .models import PlanVersion
    return PlanVersion.objects.filter(pk=version_id).first()
