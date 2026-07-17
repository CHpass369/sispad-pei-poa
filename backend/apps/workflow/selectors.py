from django.db import models
from typing import Optional


def select_envios_formulacion(unidad_id=None, gestion: Optional[int] = None, activo: Optional[bool] = None):
    """Queryset for listing envios de formulacion."""
    from .models import EnvioFormulacion
    qs = EnvioFormulacion.objects.select_related('unidad', 'enviado_por')
    if unidad_id:
        qs = qs.filter(unidad_id=unidad_id)
    if gestion:
        qs = qs.filter(gestion=gestion)
    if activo is not None:
        qs = qs.filter(activo=activo)
    return qs


def select_envio_by_id(envio_id):
    """Get single EnvioFormulacion by UUID."""
    from .models import EnvioFormulacion
    return EnvioFormulacion.objects.filter(pk=envio_id).first()


def select_revisiones(envio_id=None, tipo_revision: Optional[str] = None, estado: Optional[str] = None, revisor_id=None, resultado: Optional[str] = None):
    """Queryset for listing revisiones."""
    from .models import Revision
    qs = Revision.objects.select_related('envio', 'revisor')
    if envio_id:
        qs = qs.filter(envio_id=envio_id)
    if tipo_revision:
        qs = qs.filter(tipo_revision=tipo_revision)
    if estado:
        qs = qs.filter(estado=estado)
    if revisor_id:
        qs = qs.filter(revisor_id=revisor_id)
    if resultado:
        qs = qs.filter(resultado=resultado)
    return qs


def select_revision_by_id(revision_id):
    """Get single Revision by UUID."""
    from .models import Revision
    return Revision.objects.filter(pk=revision_id).first()


def select_observaciones(revision_id=None, tipo: Optional[str] = None, severidad: Optional[str] = None, estado: Optional[str] = None, gestion: Optional[int] = None, search: Optional[str] = None):
    """Queryset for listing observaciones."""
    from .models import Observacion
    qs = Observacion.objects.select_related('revision', 'responsable_subsanacion')
    if revision_id:
        qs = qs.filter(revision_id=revision_id)
    if tipo:
        qs = qs.filter(tipo=tipo)
    if severidad:
        qs = qs.filter(severidad=severidad)
    if estado:
        qs = qs.filter(estado=estado)
    if gestion:
        qs = qs.filter(gestion=gestion)
    if search:
        qs = qs.filter(models.Q(texto__icontains=search) | models.Q(codigo__icontains=search))
    return qs


def select_observacion_by_id(observacion_id):
    """Get single Observacion by UUID."""
    from .models import Observacion
    return Observacion.objects.filter(pk=observacion_id).first()


def select_aprobaciones(gestion: Optional[int] = None, tipo: Optional[str] = None, estado: Optional[str] = None, version: Optional[int] = None):
    """Queryset for listing aprobaciones."""
    from .models import Aprobacion
    qs = Aprobacion.objects.select_related('aprobado_por', 'documento')
    if gestion:
        qs = qs.filter(gestion=gestion)
    if tipo:
        qs = qs.filter(tipo=tipo)
    if estado:
        qs = qs.filter(estado=estado)
    if version is not None:
        qs = qs.filter(version=version)
    return qs


def select_aprobacion_by_id(aprobacion_id):
    """Get single Aprobacion by UUID."""
    from .models import Aprobacion
    return Aprobacion.objects.filter(pk=aprobacion_id).first()
