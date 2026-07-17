from django.db import models
from typing import Optional


def select_reportes_generados(tipo: Optional[str] = None, formato: Optional[str] = None, gestion: Optional[int] = None, generado_por_id=None, search: Optional[str] = None):
    """Queryset for listing reportes generados."""
    from .models import ReporteGenerado
    qs = ReporteGenerado.objects.select_related('generado_por')
    if tipo:
        qs = qs.filter(tipo=tipo)
    if formato:
        qs = qs.filter(formato=formato)
    if gestion:
        qs = qs.filter(gestion=gestion)
    if generado_por_id:
        qs = qs.filter(generado_por_id=generado_por_id)
    if search:
        qs = qs.filter(nombre__icontains=search)
    return qs


def select_reporte_by_id(reporte_id):
    """Get single ReporteGenerado by UUID."""
    from .models import ReporteGenerado
    return ReporteGenerado.objects.filter(pk=reporte_id).first()
