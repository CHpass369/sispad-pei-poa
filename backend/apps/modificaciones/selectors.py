from django.db import models
from typing import Optional


def select_solicitudes_modificacion(gestion_fiscal: Optional[int] = None, tipo: Optional[str] = None, estado: Optional[str] = None, solicitado_por_id=None, poau_id=None, search: Optional[str] = None):
    """Queryset for listing solicitudes de modificacion."""
    from .models import SolicitudModificacion
    qs = SolicitudModificacion.objects.select_related('poau', 'solicitado_por')
    if gestion_fiscal:
        qs = qs.filter(gestion_fiscal=gestion_fiscal)
    if tipo:
        qs = qs.filter(tipo=tipo)
    if estado:
        qs = qs.filter(estado=estado)
    if solicitado_por_id:
        qs = qs.filter(solicitado_por_id=solicitado_por_id)
    if poau_id:
        qs = qs.filter(poau_id=poau_id)
    if search:
        qs = qs.filter(models.Q(motivo__icontains=search) | models.Q(entidad_afectada_tipo__icontains=search))
    return qs


def select_solicitud_by_id(solicitud_id):
    """Get single SolicitudModificacion by UUID."""
    from .models import SolicitudModificacion
    return SolicitudModificacion.objects.filter(pk=solicitud_id).first()


def select_cambios_modificacion(solicitud_id=None):
    """Queryset for listing cambios de modificacion."""
    from .models import CambioModificacion
    qs = CambioModificacion.objects.select_related('solicitud')
    if solicitud_id:
        qs = qs.filter(solicitud_id=solicitud_id)
    return qs


def select_cambio_by_id(cambio_id):
    """Get single CambioModificacion by UUID."""
    from .models import CambioModificacion
    return CambioModificacion.objects.filter(pk=cambio_id).first()


def select_impactos_modificacion(solicitud_id=None):
    """Queryset for listing impactos de modificacion."""
    from .models import ImpactoModificacion
    qs = ImpactoModificacion.objects.select_related('solicitud')
    if solicitud_id:
        qs = qs.filter(solicitud_id=solicitud_id)
    return qs


def select_impacto_by_id(impacto_id):
    """Get single ImpactoModificacion by UUID."""
    from .models import ImpactoModificacion
    return ImpactoModificacion.objects.filter(pk=impacto_id).first()


def select_impacto_by_solicitud(solicitud_id):
    """Get impacto for a specific solicitud."""
    from .models import ImpactoModificacion
    return ImpactoModificacion.objects.filter(solicitud_id=solicitud_id).first()
