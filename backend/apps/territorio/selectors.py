from django.db import models
from typing import Optional


def select_distritos(search: Optional[str] = None):
    """Queryset for listing distritos."""
    from .models import Distrito
    qs = Distrito.objects.all()
    if search:
        qs = qs.filter(models.Q(nombre__icontains=search) | models.Q(codigo__icontains=search))
    return qs


def select_distrito_by_id(distrito_id):
    """Get single Distrito by UUID."""
    from .models import Distrito
    return Distrito.objects.filter(pk=distrito_id).first()


def select_unidades_territoriales(tipo: Optional[str] = None, distrito_id=None, search: Optional[str] = None):
    """Queryset for listing unidades territoriales."""
    from .models import UnidadTerritorial
    qs = UnidadTerritorial.objects.select_related('distrito')
    if tipo:
        qs = qs.filter(tipo=tipo)
    if distrito_id:
        qs = qs.filter(distrito_id=distrito_id)
    if search:
        qs = qs.filter(models.Q(nombre__icontains=search) | models.Q(codigo__icontains=search))
    return qs


def select_unidad_territorial_by_id(ut_id):
    """Get single UnidadTerritorial by UUID."""
    from .models import UnidadTerritorial
    return UnidadTerritorial.objects.filter(pk=ut_id).first()


def select_localizaciones(entidad: Optional[str] = None, entidad_id: Optional[str] = None, distrito_id=None, unidad_territorial_id=None, gestion: Optional[int] = None, activo: Optional[bool] = None):
    """Queryset for listing localizaciones territoriales."""
    from .models import LocalizacionTerritorial
    qs = LocalizacionTerritorial.objects.select_related('distrito', 'unidad_territorial')
    if entidad:
        qs = qs.filter(entidad=entidad)
    if entidad_id:
        qs = qs.filter(entidad_id=entidad_id)
    if distrito_id:
        qs = qs.filter(distrito_id=distrito_id)
    if unidad_territorial_id:
        qs = qs.filter(unidad_territorial_id=unidad_territorial_id)
    if gestion:
        qs = qs.filter(gestion=gestion)
    if activo is not None:
        qs = qs.filter(activo=activo)
    return qs


def select_localizacion_by_id(localizacion_id):
    """Get single LocalizacionTerritorial by UUID."""
    from .models import LocalizacionTerritorial
    return LocalizacionTerritorial.objects.filter(pk=localizacion_id).first()
