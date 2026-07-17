from django.db import models
from typing import Optional


def select_versiones_normativa(gestion: Optional[int] = None, tipo: Optional[str] = None, activo: Optional[bool] = None, search: Optional[str] = None):
    """Queryset for listing versiones normativas."""
    from .models import VersionNormativa
    qs = VersionNormativa.objects.all()
    if gestion:
        qs = qs.filter(gestion=gestion)
    if tipo:
        qs = qs.filter(tipo=tipo)
    if activo is not None:
        qs = qs.filter(activo=activo)
    if search:
        qs = qs.filter(models.Q(titulo__icontains=search) | models.Q(numero__icontains=search))
    return qs


def select_version_normativa_by_id(normativa_id):
    """Get single VersionNormativa by UUID."""
    from .models import VersionNormativa
    return VersionNormativa.objects.filter(pk=normativa_id).first()


def select_reglas_presupuestarias(tipo: Optional[str] = None, severidad: Optional[str] = None, gestion: Optional[int] = None, activo: Optional[bool] = None):
    """Queryset for listing reglas presupuestarias legales."""
    from .models import ReglaPresupuestariaLegal
    qs = ReglaPresupuestariaLegal.objects.all()
    if tipo:
        qs = qs.filter(tipo=tipo)
    if severidad:
        qs = qs.filter(severidad=severidad)
    if gestion:
        qs = qs.filter(gestion_desde__lte=gestion).filter(
            models.Q(gestion_hasta__isnull=True) | models.Q(gestion_hasta__gte=gestion)
        )
    if activo is not None:
        qs = qs.filter(activo=activo)
    return qs


def select_regla_by_id(regla_id):
    """Get single ReglaPresupuestariaLegal by UUID."""
    from .models import ReglaPresupuestariaLegal
    return ReglaPresupuestariaLegal.objects.filter(pk=regla_id).first()


def select_regla_by_codigo(codigo: str):
    """Get single ReglaPresupuestariaLegal by codigo."""
    from .models import ReglaPresupuestariaLegal
    return ReglaPresupuestariaLegal.objects.filter(codigo=codigo).first()
