from django.db import models
from typing import Optional, Type


def select_active_objects(queryset: models.QuerySet) -> models.QuerySet:
    """Filter queryset to only active objects."""
    return queryset.filter(activo=True)


def select_by_gestion(queryset: models.QuerySet, gestion: int) -> models.QuerySet:
    """Filter queryset by gestion field."""
    return queryset.filter(gestion=gestion)


def select_by_vigencia(queryset: models.QuerySet, fecha=None) -> models.QuerySet:
    """Filter queryset to objects valid at a given date."""
    if fecha is None:
        from django.utils import timezone
        fecha = timezone.now().date()
    return queryset.filter(
        fecha_vigencia_desde__lte=fecha
    ).filter(
        models.Q(fecha_vigencia_hasta__isnull=True) | models.Q(fecha_vigencia_hasta__gte=fecha)
    )


def select_by_version(queryset: models.QuerySet, gestion: int, version: Optional[int] = None) -> models.QuerySet:
    """Filter queryset by gestion and optionally by version."""
    qs = queryset.filter(gestion=gestion)
    if version is not None:
        qs = qs.filter(version=version)
    return qs
