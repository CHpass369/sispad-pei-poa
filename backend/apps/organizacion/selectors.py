from django.db import models
from typing import Optional


def select_tipos_unidad(codigo: Optional[str] = None, activo: Optional[bool] = None, nivel: Optional[int] = None):
    """Queryset for listing tipos de unidad."""
    from .models import TipoUnidad
    qs = TipoUnidad.objects.all()
    if codigo:
        qs = qs.filter(codigo=codigo)
    if activo is not None:
        qs = qs.filter(activo=activo)
    if nivel is not None:
        qs = qs.filter(nivel=nivel)
    return qs


def select_tipo_unidad_by_id(tipo_id):
    """Get single TipoUnidad by UUID."""
    from .models import TipoUnidad
    return TipoUnidad.objects.filter(pk=tipo_id).first()


def select_unidades_organizacionales(gestion: Optional[int] = None, tipo_id=None, padre_id=None, activo: Optional[bool] = None, search: Optional[str] = None):
    """Queryset for listing unidades organizacionales."""
    from .models import UnidadOrganizacional
    qs = UnidadOrganizacional.objects.select_related('tipo', 'padre', 'responsable')
    if gestion:
        qs = qs.filter(gestion=gestion)
    if tipo_id:
        qs = qs.filter(tipo_id=tipo_id)
    if padre_id:
        qs = qs.filter(padre_id=padre_id)
    if activo is not None:
        qs = qs.filter(activo=activo)
    if search:
        qs = qs.filter(models.Q(nombre__icontains=search) | models.Q(codigo__icontains=search))
    return qs


def select_unidad_organizacional_by_id(unidad_id):
    """Get single UnidadOrganizacional by UUID."""
    from .models import UnidadOrganizacional
    return UnidadOrganizacional.objects.filter(pk=unidad_id).first()


def select_direcciones_administrativas(gestion: Optional[int] = None, activo: Optional[bool] = None):
    """Queryset for listing direcciones administrativas."""
    from .models import DireccionAdministrativa
    qs = DireccionAdministrativa.objects.select_related('responsable')
    if gestion:
        qs = qs.filter(gestion=gestion)
    if activo is not None:
        qs = qs.filter(activo=activo)
    return qs


def select_direccion_administrativa_by_id(da_id):
    """Get single DireccionAdministrativa by UUID."""
    from .models import DireccionAdministrativa
    return DireccionAdministrativa.objects.filter(pk=da_id).first()


def select_unidades_ejecutoras(da_id=None, gestion: Optional[int] = None, activo: Optional[bool] = None):
    """Queryset for listing unidades ejecutoras."""
    from .models import UnidadEjecutora
    qs = UnidadEjecutora.objects.select_related('da', 'unidad_organizacional', 'responsable')
    if da_id:
        qs = qs.filter(da_id=da_id)
    if gestion:
        qs = qs.filter(gestion=gestion)
    if activo is not None:
        qs = qs.filter(activo=activo)
    return qs


def select_unidad_ejecutora_by_id(ue_id):
    """Get single UnidadEjecutora by UUID."""
    from .models import UnidadEjecutora
    return UnidadEjecutora.objects.filter(pk=ue_id).first()


def select_asignaciones_usuario(usuario_id=None, unidad_id=None, gestion: Optional[int] = None, activo: Optional[bool] = None):
    """Queryset for listing asignaciones usuario-unidad."""
    from .models import AsignacionUsuarioUnidad
    qs = AsignacionUsuarioUnidad.objects.select_related('usuario', 'unidad')
    if usuario_id:
        qs = qs.filter(usuario_id=usuario_id)
    if unidad_id:
        qs = qs.filter(unidad_id=unidad_id)
    if gestion:
        qs = qs.filter(gestion=gestion)
    if activo is not None:
        qs = qs.filter(activo=activo)
    return qs


def select_asignacion_by_id(asignacion_id):
    """Get single AsignacionUsuarioUnidad by UUID."""
    from .models import AsignacionUsuarioUnidad
    return AsignacionUsuarioUnidad.objects.filter(pk=asignacion_id).first()


def select_responsables_poa(gestion: Optional[int] = None):
    """Get users who are POA responsible for their units in a given gestion."""
    from .models import AsignacionUsuarioUnidad
    qs = AsignacionUsuarioUnidad.objects.filter(es_responsable_poa=True, activo=True)
    if gestion:
        qs = qs.filter(gestion=gestion)
    return qs.select_related('usuario', 'unidad')
