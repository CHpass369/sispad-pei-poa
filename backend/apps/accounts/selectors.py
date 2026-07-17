from django.db import models
from django.db.models import QuerySet
from typing import Optional


def select_roles(codigo: Optional[str] = None, activo: Optional[bool] = None):
    """Queryset for listing roles with optional filters."""
    from .models import Rol
    qs = Rol.objects.all()
    if codigo:
        qs = qs.filter(codigo=codigo)
    if activo is not None:
        qs = qs.filter(activo=activo)
    return qs


def select_rol_by_id(rol_id):
    """Get single rol by UUID."""
    from .models import Rol
    return Rol.objects.filter(pk=rol_id).first()


def select_usuarios(email: Optional[str] = None, activo: Optional[bool] = None, search: Optional[str] = None, rol_codigo: Optional[str] = None):
    """Queryset for listing usuarios with optional filters."""
    from .models import Usuario
    qs = Usuario.objects.all()
    if email:
        qs = qs.filter(email__iexact=email)
    if activo is not None:
        qs = qs.filter(activo=activo)
    if search:
        qs = qs.filter(
            models.Q(first_name__icontains=search) |
            models.Q(last_name__icontains=search) |
            models.Q(email__icontains=search)
        )
    if rol_codigo:
        qs = qs.filter(roles__codigo=rol_codigo)
    return qs.distinct()


def select_usuario_by_id(usuario_id):
    """Get single usuario by UUID."""
    from .models import Usuario
    return Usuario.objects.filter(pk=usuario_id).first()


def select_usuario_by_email(email: str):
    """Get single usuario by email."""
    from .models import Usuario
    return Usuario.objects.filter(email__iexact=email).first()
