from django.db import models
from typing import Optional


def select_sectores_pad(search: Optional[str] = None):
    """Queryset for listing sectores del PAD."""
    from .models import SectorPAD
    qs = SectorPAD.objects.all()
    if search:
        qs = qs.filter(models.Q(nombre__icontains=search) | models.Q(codigo__icontains=search))
    return qs


def select_sector_pad_by_id(sector_id):
    """Get single SectorPAD by PK."""
    from .models import SectorPAD
    return SectorPAD.objects.filter(pk=sector_id).first()


def select_politicas_pad(gestion: Optional[int] = None, search: Optional[str] = None):
    """Queryset for listing politicas del PAD."""
    from .models import PoliticaPAD
    qs = PoliticaPAD.objects.all()
    if gestion:
        qs = qs.filter(gestion=gestion)
    if search:
        qs = qs.filter(models.Q(nombre__icontains=search) | models.Q(codigo__icontains=search))
    return qs


def select_politica_pad_by_id(politica_id):
    """Get single PoliticaPAD by PK."""
    from .models import PoliticaPAD
    return PoliticaPAD.objects.filter(pk=politica_id).first()


def select_lineamientos_estrategicos(politica_id=None, gestion: Optional[int] = None, search: Optional[str] = None):
    """Queryset for listing lineamientos estrategicos."""
    from .models import LineamientoEstrategico
    qs = LineamientoEstrategico.objects.select_related('politica')
    if politica_id:
        qs = qs.filter(politica_id=politica_id)
    if gestion:
        qs = qs.filter(gestion=gestion)
    if search:
        qs = qs.filter(models.Q(nombre__icontains=search) | models.Q(codigo__icontains=search))
    return qs


def select_lineamiento_by_id(lineamiento_id):
    """Get single LineamientoEstrategico by PK."""
    from .models import LineamientoEstrategico
    return LineamientoEstrategico.objects.filter(pk=lineamiento_id).first()


def select_resultados_territoriales(gestion: Optional[int] = None, estado: Optional[str] = None, lineamiento_id=None, sector_id=None, search: Optional[str] = None):
    """Queryset for listing resultados territoriales."""
    from .models import ResultadoTerritorial
    qs = ResultadoTerritorial.objects.select_related('lineamiento', 'sector')
    if gestion:
        qs = qs.filter(gestion=gestion)
    if estado:
        qs = qs.filter(estado=estado)
    if lineamiento_id:
        qs = qs.filter(lineamiento_id=lineamiento_id)
    if sector_id:
        qs = qs.filter(sector_id=sector_id)
    if search:
        qs = qs.filter(models.Q(nombre__icontains=search) | models.Q(codigo__icontains=search))
    return qs


def select_resultado_territorial_by_id(resultado_id):
    """Get single ResultadoTerritorial by PK."""
    from .models import ResultadoTerritorial
    return ResultadoTerritorial.objects.filter(pk=resultado_id).first()


def select_articulacion_log(entidad: Optional[str] = None, entidad_id: Optional[str] = None, accion: Optional[str] = None):
    """Queryset for listing articulacion logs."""
    from .models import ArticulacionLog
    qs = ArticulacionLog.objects.select_related('usuario')
    if entidad:
        qs = qs.filter(entidad=entidad)
    if entidad_id:
        qs = qs.filter(entidad_id=entidad_id)
    if accion:
        qs = qs.filter(accion=accion)
    return qs


def select_productos_territoriales(resultado_id=None, gestion: Optional[int] = None, search: Optional[str] = None):
    """Queryset for listing productos territoriales."""
    from .models import ProductoTerritorial
    qs = ProductoTerritorial.objects.select_related('resultado')
    if resultado_id:
        qs = qs.filter(resultado_id=resultado_id)
    if gestion:
        qs = qs.filter(gestion=gestion)
    if search:
        qs = qs.filter(models.Q(nombre__icontains=search) | models.Q(codigo__icontains=search))
    return qs


def select_producto_territorial_by_id(producto_id):
    """Get single ProductoTerritorial by PK."""
    from .models import ProductoTerritorial
    return ProductoTerritorial.objects.filter(pk=producto_id).first()


def select_programaciones_anuales_pad(resultado_id=None, producto_id=None, anio: Optional[int] = None, tipo: Optional[str] = None):
    """Queryset for listing programaciones anuales PAD."""
    from .models import ProgramacionAnualPAD
    qs = ProgramacionAnualPAD.objects.select_related('resultado', 'producto')
    if resultado_id:
        qs = qs.filter(resultado_id=resultado_id)
    if producto_id:
        qs = qs.filter(producto_id=producto_id)
    if anio:
        qs = qs.filter(anio=anio)
    if tipo:
        qs = qs.filter(tipo=tipo)
    return qs


def select_programacion_anual_pad_by_id(programacion_id):
    """Get single ProgramacionAnualPAD by PK."""
    from .models import ProgramacionAnualPAD
    return ProgramacionAnualPAD.objects.filter(pk=programacion_id).first()


def select_articulaciones_sipeb(resultado_id=None, gestion: Optional[int] = None, cod_ods: Optional[str] = None, cod_sector: Optional[str] = None):
    """Queryset for listing articulaciones SIPEB."""
    from .models import ArticulacionSIPEB
    qs = ArticulacionSIPEB.objects.select_related('resultado')
    if resultado_id:
        qs = qs.filter(resultado_id=resultado_id)
    if gestion:
        qs = qs.filter(gestion=gestion)
    if cod_ods:
        qs = qs.filter(cod_ods=cod_ods)
    if cod_sector:
        qs = qs.filter(cod_sector=cod_sector)
    return qs


def select_articulacion_sipeb_by_id(articulacion_id):
    """Get single ArticulacionSIPEB by PK."""
    from .models import ArticulacionSIPEB
    return ArticulacionSIPEB.objects.filter(pk=articulacion_id).first()
