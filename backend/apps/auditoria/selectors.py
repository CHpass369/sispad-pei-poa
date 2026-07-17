from django.db import models
from typing import Optional


def select_eventos_auditoria(usuario_id=None, accion: Optional[str] = None, entidad: Optional[str] = None, entidad_id: Optional[str] = None, gestion: Optional[int] = None, search: Optional[str] = None):
    """Queryset for listing eventos de auditoria."""
    from .models import EventoAuditoria
    qs = EventoAuditoria.objects.select_related('usuario')
    if usuario_id:
        qs = qs.filter(usuario_id=usuario_id)
    if accion:
        qs = qs.filter(accion=accion)
    if entidad:
        qs = qs.filter(entidad=entidad)
    if entidad_id:
        qs = qs.filter(entidad_id=entidad_id)
    if gestion:
        qs = qs.filter(gestion=gestion)
    if search:
        qs = qs.filter(models.Q(resumen__icontains=search) | models.Q(entidad__icontains=search))
    return qs


def select_evento_by_id(evento_id):
    """Get single EventoAuditoria by UUID."""
    from .models import EventoAuditoria
    return EventoAuditoria.objects.filter(pk=evento_id).first()


def select_eventos_por_entidad(entidad: str, entidad_id: str):
    """Get all audit events for a specific entity."""
    from .models import EventoAuditoria
    return EventoAuditoria.objects.filter(
        entidad=entidad, entidad_id=entidad_id
    ).select_related('usuario').order_by('-creado_en')
