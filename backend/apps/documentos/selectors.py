from django.db import models
from typing import Optional


def select_documentos_adjuntos(entidad: Optional[str] = None, entidad_id: Optional[str] = None, gestion: Optional[int] = None, tipo_documento: Optional[str] = None, activo: Optional[bool] = None, subido_por_id=None):
    """Queryset for listing documentos adjuntos."""
    from .models import DocumentoAdjunto
    qs = DocumentoAdjunto.objects.select_related('subido_por')
    if entidad:
        qs = qs.filter(entidad=entidad)
    if entidad_id:
        qs = qs.filter(entidad_id=entidad_id)
    if gestion:
        qs = qs.filter(gestion=gestion)
    if tipo_documento:
        qs = qs.filter(tipo_documento=tipo_documento)
    if activo is not None:
        qs = qs.filter(activo=activo)
    if subido_por_id:
        qs = qs.filter(subido_por_id=subido_por_id)
    return qs


def select_documento_by_id(documento_id):
    """Get single DocumentoAdjunto by UUID."""
    from .models import DocumentoAdjunto
    return DocumentoAdjunto.objects.filter(pk=documento_id).first()


def select_documentos_por_entidad(entidad: str, entidad_id: str, gestion: Optional[int] = None):
    """Get all documents for a specific entity."""
    from .models import DocumentoAdjunto
    qs = DocumentoAdjunto.objects.filter(entidad=entidad, entidad_id=entidad_id, activo=True)
    if gestion:
        qs = qs.filter(gestion=gestion)
    return qs.select_related('subido_por')
