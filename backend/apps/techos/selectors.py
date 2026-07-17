from django.db import models
from typing import Optional


def select_techos_presupuestarios(gestion: Optional[int] = None, fuente_id=None, organismo_id=None, activo: Optional[bool] = None, version: Optional[int] = None):
    """Queryset for listing techos presupuestarios."""
    from .models import TechoPresupuestario
    qs = TechoPresupuestario.objects.select_related('fuente', 'organismo')
    if gestion:
        qs = qs.filter(gestion=gestion)
    if fuente_id:
        qs = qs.filter(fuente_id=fuente_id)
    if organismo_id:
        qs = qs.filter(organismo_id=organismo_id)
    if activo is not None:
        qs = qs.filter(activo=activo)
    if version is not None:
        qs = qs.filter(version=version)
    return qs


def select_techo_by_id(techo_id):
    """Get single TechoPresupuestario by UUID."""
    from .models import TechoPresupuestario
    return TechoPresupuestario.objects.filter(pk=techo_id).first()


def select_distribuciones_techo(techo_id=None, da_id=None, ue_id=None, unidad_id=None, programa_id=None, activo: Optional[bool] = None):
    """Queryset for listing distribuciones de techo."""
    from .models import DistribucionTecho
    qs = DistribucionTecho.objects.select_related('techo', 'da', 'ue', 'unidad', 'programa')
    if techo_id:
        qs = qs.filter(techo_id=techo_id)
    if da_id:
        qs = qs.filter(da_id=da_id)
    if ue_id:
        qs = qs.filter(ue_id=ue_id)
    if unidad_id:
        qs = qs.filter(unidad_id=unidad_id)
    if programa_id:
        qs = qs.filter(programa_id=programa_id)
    if activo is not None:
        qs = qs.filter(activo=activo)
    return qs


def select_distribucion_by_id(distribucion_id):
    """Get single DistribucionTecho by UUID."""
    from .models import DistribucionTecho
    return DistribucionTecho.objects.filter(pk=distribucion_id).first()


def select_movimientos_techo(techo_id=None, movement_type: Optional[str] = None, search: Optional[str] = None):
    """Queryset for listing movimientos de techo."""
    from .models import MovimientoTecho
    qs = MovimientoTecho.objects.select_related('techo', 'source_ceiling', 'destination_ceiling', 'requested_by', 'approved_by')
    if techo_id:
        qs = qs.filter(techo_id=techo_id)
    if movement_type:
        qs = qs.filter(movement_type=movement_type)
    return qs


def select_movimiento_by_id(movimiento_id):
    """Get single MovimientoTecho by UUID."""
    from .models import MovimientoTecho
    return MovimientoTecho.objects.filter(pk=movimiento_id).first()
