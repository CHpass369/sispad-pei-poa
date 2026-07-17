from django.db import models
from typing import Optional


def select_acciones_correctivas(gestion: Optional[int] = None, status: Optional[str] = None, responsible_id=None, responsible_unit_id=None, alerta_id=None, entry_id=None, search: Optional[str] = None):
    """Queryset for listing acciones correctivas."""
    from .models import AccionCorrectiva
    qs = AccionCorrectiva.objects.select_related('alerta', 'entry', 'responsible', 'responsible_unit', 'verified_by')
    if gestion:
        qs = qs.filter(gestion=gestion)
    if status:
        qs = qs.filter(status=status)
    if responsible_id:
        qs = qs.filter(responsible_id=responsible_id)
    if responsible_unit_id:
        qs = qs.filter(responsible_unit_id=responsible_unit_id)
    if alerta_id:
        qs = qs.filter(alerta_id=alerta_id)
    if entry_id:
        qs = qs.filter(entry_id=entry_id)
    if search:
        qs = qs.filter(models.Q(description__icontains=search) | models.Q(cause__icontains=search))
    return qs


def select_accion_correctiva_by_id(accion_id):
    """Get single AccionCorrectiva by UUID."""
    from .models import AccionCorrectiva
    return AccionCorrectiva.objects.filter(pk=accion_id).first()


def select_acciones_correctivas_vencidas():
    """Get overdue acciones correctivas."""
    from .models import AccionCorrectiva
    from django.utils import timezone
    return AccionCorrectiva.objects.filter(
        status__in=['pendiente', 'en_ejecucion'],
        due_date__lt=timezone.now().date(),
    ).select_related('responsible', 'responsible_unit')


def select_compromisos(accion_correctiva_id=None, status: Optional[str] = None):
    """Queryset for listing compromisos de accion correctiva."""
    from .models import CompromisoAccionCorrectiva
    qs = CompromisoAccionCorrectiva.objects.select_related('accion_correctiva')
    if accion_correctiva_id:
        qs = qs.filter(accion_correctiva_id=accion_correctiva_id)
    if status:
        qs = qs.filter(status=status)
    return qs


def select_compromiso_by_id(compromiso_id):
    """Get single CompromisoAccionCorrectiva by UUID."""
    from .models import CompromisoAccionCorrectiva
    return CompromisoAccionCorrectiva.objects.filter(pk=compromiso_id).first()
