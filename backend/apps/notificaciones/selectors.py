from django.db import models
from typing import Optional


def select_tipos_notificacion(codigo: Optional[str] = None, is_active: Optional[bool] = None, search: Optional[str] = None):
    """Queryset for listing tipos de notificacion."""
    from .models import TipoNotificacion
    qs = TipoNotificacion.objects.all()
    if codigo:
        qs = qs.filter(codigo=codigo)
    if is_active is not None:
        qs = qs.filter(is_active=is_active)
    if search:
        qs = qs.filter(models.Q(nombre__icontains=search) | models.Q(codigo__icontains=search))
    return qs


def select_tipo_notificacion_by_id(tipo_id):
    """Get single TipoNotificacion by UUID."""
    from .models import TipoNotificacion
    return TipoNotificacion.objects.filter(pk=tipo_id).first()


def select_tipo_notificacion_by_codigo(codigo: str):
    """Get single TipoNotificacion by codigo."""
    from .models import TipoNotificacion
    return TipoNotificacion.objects.filter(codigo=codigo).first()


def select_notificaciones(user_id=None, gestion: Optional[int] = None, is_read: Optional[bool] = None, priority: Optional[str] = None, entity_type: Optional[str] = None):
    """Queryset for listing notificaciones."""
    from .models import Notificacion
    qs = Notificacion.objects.select_related('user', 'tipo')
    if user_id:
        qs = qs.filter(user_id=user_id)
    if gestion:
        qs = qs.filter(gestion=gestion)
    if is_read is not None:
        qs = qs.filter(is_read=is_read)
    if priority:
        qs = qs.filter(priority=priority)
    if entity_type:
        qs = qs.filter(entity_type=entity_type)
    return qs


def select_notificacion_by_id(notificacion_id):
    """Get single Notificacion by UUID."""
    from .models import Notificacion
    return Notificacion.objects.filter(pk=notificacion_id).first()


def select_notificaciones_no_leidas(user_id):
    """Get unread notifications for a user."""
    from .models import Notificacion
    return Notificacion.objects.filter(
        user_id=user_id, is_read=False
    ).select_related('tipo').order_by('-created_at')


def select_preferencia_notificacion(user_id):
    """Get notification preferences for a user."""
    from .models import PreferenciaNotificacion
    return PreferenciaNotificacion.objects.filter(user_id=user_id).first()
