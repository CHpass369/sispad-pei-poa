from django.db import models
from typing import Optional


def select_reportes_seguimiento(gestion: Optional[int] = None, periodo: Optional[str] = None, unidad_id=None, estado: Optional[str] = None):
    """Queryset for listing reportes de seguimiento."""
    from .models import ReporteSeguimiento
    qs = ReporteSeguimiento.objects.select_related('unidad_organizacional', 'submitted_by', 'approved_by')
    if gestion:
        qs = qs.filter(gestion=gestion)
    if periodo:
        qs = qs.filter(periodo=periodo)
    if unidad_id:
        qs = qs.filter(unidad_organizacional_id=unidad_id)
    if estado:
        qs = qs.filter(estado=estado)
    return qs


def select_reporte_seguimiento_by_id(reporte_id):
    """Get single ReporteSeguimiento by UUID."""
    from .models import ReporteSeguimiento
    return ReporteSeguimiento.objects.filter(pk=reporte_id).first()


def select_entradas_seguimiento(reporte_id=None, actividad_id=None):
    """Queryset for listing entradas de seguimiento."""
    from .models import EntradaSeguimiento
    qs = EntradaSeguimiento.objects.select_related('reporte', 'actividad')
    if reporte_id:
        qs = qs.filter(reporte_id=reporte_id)
    if actividad_id:
        qs = qs.filter(actividad_id=actividad_id)
    return qs


def select_entrada_seguimiento_by_id(entrada_id):
    """Get single EntradaSeguimiento by UUID."""
    from .models import EntradaSeguimiento
    return EntradaSeguimiento.objects.filter(pk=entrada_id).first()


def select_alertas(entrada_id=None, tipo: Optional[str] = None, severidad: Optional[str] = None, activa: Optional[bool] = None, resuelta_por_id=None):
    """Queryset for listing alertas."""
    from .models import Alerta
    qs = Alerta.objects.select_related('entrada', 'resuelta_por')
    if entrada_id:
        qs = qs.filter(entrada_id=entrada_id)
    if tipo:
        qs = qs.filter(tipo=tipo)
    if severidad:
        qs = qs.filter(severidad=severidad)
    if activa is not None:
        qs = qs.filter(activa=activa)
    if resuelta_por_id:
        qs = qs.filter(resuelta_por_id=resuelta_por_id)
    return qs


def select_alerta_by_id(alerta_id):
    """Get single Alerta by UUID."""
    from .models import Alerta
    return Alerta.objects.filter(pk=alerta_id).first()


def select_alertas_activas(tipo: Optional[str] = None, severidad: Optional[str] = None):
    """Get active alerts."""
    from .models import Alerta
    qs = Alerta.objects.filter(activa=True).select_related('entrada')
    if tipo:
        qs = qs.filter(tipo=tipo)
    if severidad:
        qs = qs.filter(severidad=severidad)
    return qs


def select_umbrales_configuracion(tipo_umbral: Optional[str] = None, activo: Optional[bool] = None):
    """Queryset for listing umbrales de configuracion."""
    from .models import UmbralConfiguracion
    qs = UmbralConfiguracion.objects.all()
    if tipo_umbral:
        qs = qs.filter(tipo_umbral=tipo_umbral)
    if activo is not None:
        qs = qs.filter(activo=activo)
    return qs


def select_umbral_by_id(umbral_id):
    """Get single UmbralConfiguracion by UUID."""
    from .models import UmbralConfiguracion
    return UmbralConfiguracion.objects.filter(pk=umbral_id).first()
