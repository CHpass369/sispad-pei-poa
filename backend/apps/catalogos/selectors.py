from django.db import models
from typing import Optional, Type


def _select_catalogo_items(model_class: Type[models.Model], gestion: Optional[int] = None, activo: Optional[bool] = None, search: Optional[str] = None, codigo: Optional[str] = None):
    """Generic selector for all CatalogoBase subclasses."""
    qs = model_class.objects.all()
    if gestion:
        qs = qs.filter(gestion=gestion)
    if activo is not None:
        qs = qs.filter(activo=activo)
    if search:
        qs = qs.filter(models.Q(denominacion__icontains=search) | models.Q(codigo__icontains=search))
    if codigo:
        qs = qs.filter(codigo__startswith=codigo)
    return qs


def select_clasificadores_institucionales(gestion=None, activo=None, search=None, codigo=None):
    from .models import ClasificadorInstitucional
    return _select_catalogo_items(ClasificadorInstitucional, gestion, activo, search, codigo)


def select_rubros_recurso(gestion=None, activo=None, search=None, codigo=None):
    from .models import RubroRecurso
    return _select_catalogo_items(RubroRecurso, gestion, activo, search, codigo)


def select_objetos_gasto(gestion=None, activo=None, search=None, codigo=None):
    from .models import ObjetoGasto
    return _select_catalogo_items(ObjetoGasto, gestion, activo, search, codigo)


def select_fuentes_financiamiento(gestion=None, activo=None, search=None, codigo=None):
    from .models import FuenteFinanciamiento
    return _select_catalogo_items(FuenteFinanciamiento, gestion, activo, search, codigo)


def select_organismos_financiadores(gestion=None, activo=None, search=None, codigo=None):
    from .models import OrganismoFinanciador
    return _select_catalogo_items(OrganismoFinanciador, gestion, activo, search, codigo)


def select_entidades_transferencia(gestion=None, activo=None, search=None, codigo=None):
    from .models import EntidadTransferencia
    return _select_catalogo_items(EntidadTransferencia, gestion, activo, search, codigo)


def select_finalidades_funcion(gestion=None, activo=None, search=None, codigo=None):
    from .models import FinalidadFuncion
    return _select_catalogo_items(FinalidadFuncion, gestion, activo, search, codigo)


def select_unidades_medida(gestion=None, activo=None, search=None, codigo=None):
    from .models import UnidadMedida
    return _select_catalogo_items(UnidadMedida, gestion, activo, search, codigo)


def select_tipos_operacion(gestion=None, activo=None, search=None, codigo=None):
    from .models import TipoOperacion
    return _select_catalogo_items(TipoOperacion, gestion, activo, search, codigo)


def select_tipos_producto(gestion=None, activo=None, search=None, codigo=None):
    from .models import TipoProducto
    return _select_catalogo_items(TipoProducto, gestion, activo, search, codigo)


def select_tipos_proyecto(gestion=None, activo=None, search=None, codigo=None):
    from .models import TipoProyecto
    return _select_catalogo_items(TipoProyecto, gestion, activo, search, codigo)


def select_tipos_financiamiento(gestion=None, activo=None, search=None, codigo=None):
    from .models import TipoFinanciamiento
    return _select_catalogo_items(TipoFinanciamiento, gestion, activo, search, codigo)


def select_versiones_catalogo(gestion: Optional[int] = None, aplicado: Optional[bool] = None):
    from .models import VersionCatalogo
    qs = VersionCatalogo.objects.all()
    if gestion:
        qs = qs.filter(gestion=gestion)
    if aplicado is not None:
        qs = qs.filter(aplicado=aplicado)
    return qs


def select_version_catalogo_by_id(version_id):
    from .models import VersionCatalogo
    return VersionCatalogo.objects.filter(pk=version_id).first()
