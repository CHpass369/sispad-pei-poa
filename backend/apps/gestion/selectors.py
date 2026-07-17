from django.db import models
from typing import Optional


def select_gestiones(estado: Optional[str] = None, activa: Optional[bool] = None, anio: Optional[int] = None):
    """Queryset for listing gestiones fiscales."""
    from .models import GestionFiscal
    qs = GestionFiscal.objects.select_related('creado_por')
    if estado:
        qs = qs.filter(estado=estado)
    if activa is not None:
        qs = qs.filter(activa=activa)
    if anio:
        qs = qs.filter(anio=anio)
    return qs


def select_gestion_by_id(gestion_id):
    """Get single GestionFiscal by UUID."""
    from .models import GestionFiscal
    return GestionFiscal.objects.filter(pk=gestion_id).first()


def select_gestion_by_anio(anio: int):
    """Get single GestionFiscal by anio."""
    from .models import GestionFiscal
    return GestionFiscal.objects.filter(anio=anio).first()


def select_gestion_activa():
    """Get the current active gestion."""
    from .models import GestionFiscal
    return GestionFiscal.objects.filter(activa=True).order_by('-anio').first()


def select_ciclos_formulacion(gestion_id=None, activo: Optional[bool] = None):
    """Queryset for listing ciclos de formulacion."""
    from .models import CicloFormulacion
    qs = CicloFormulacion.objects.select_related('gestion')
    if gestion_id:
        qs = qs.filter(gestion_id=gestion_id)
    if activo is not None:
        qs = qs.filter(activo=activo)
    return qs


def select_ciclo_by_id(ciclo_id):
    """Get single CicloFormulacion by UUID."""
    from .models import CicloFormulacion
    return CicloFormulacion.objects.filter(pk=ciclo_id).first()


def select_etapas_formulacion(ciclo_id=None, completada: Optional[bool] = None):
    """Queryset for listing etapas de formulacion."""
    from .models import EtapaFormulacion
    qs = EtapaFormulacion.objects.select_related('ciclo')
    if ciclo_id:
        qs = qs.filter(ciclo_id=ciclo_id)
    if completada is not None:
        qs = qs.filter(completada=completada)
    return qs


def select_etapa_by_id(etapa_id):
    """Get single EtapaFormulacion by UUID."""
    from .models import EtapaFormulacion
    return EtapaFormulacion.objects.filter(pk=etapa_id).first()
