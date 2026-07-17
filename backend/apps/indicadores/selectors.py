from django.db import models
from typing import Optional


def select_indicadores(activo: Optional[bool] = None, tipo_comportamiento: Optional[str] = None, search: Optional[str] = None, responsable_id=None):
    """Queryset for listing indicadores."""
    from .models import Indicador
    qs = Indicador.objects.select_related('unidad_medida', 'responsable')
    if activo is not None:
        qs = qs.filter(activo=activo)
    if tipo_comportamiento:
        qs = qs.filter(tipo_comportamiento=tipo_comportamiento)
    if search:
        qs = qs.filter(models.Q(nombre__icontains=search) | models.Q(codigo__icontains=search))
    if responsable_id:
        qs = qs.filter(responsable_id=responsable_id)
    return qs


def select_indicador_by_id(indicador_id):
    """Get single Indicador by UUID."""
    from .models import Indicador
    return Indicador.objects.filter(pk=indicador_id).first()


def select_metas_programadas(indicador_id=None, gestion: Optional[int] = None, version: Optional[int] = None):
    """Queryset for listing metas programadas."""
    from .models import MetaProgramada
    qs = MetaProgramada.objects.select_related('indicador')
    if indicador_id:
        qs = qs.filter(indicador_id=indicador_id)
    if gestion:
        qs = qs.filter(gestion=gestion)
    if version is not None:
        qs = qs.filter(version=version)
    return qs


def select_meta_programada_by_id(meta_id):
    """Get single MetaProgramada by UUID."""
    from .models import MetaProgramada
    return MetaProgramada.objects.filter(pk=meta_id).first()


def select_operaciones(accion_corto_plazo_id=None, activo: Optional[bool] = None, search: Optional[str] = None):
    """Queryset for listing operaciones."""
    from .models import Operacion
    qs = Operacion.objects.select_related('accion_corto_plazo', 'tipo')
    if accion_corto_plazo_id:
        qs = qs.filter(accion_corto_plazo_id=accion_corto_plazo_id)
    if activo is not None:
        qs = qs.filter(activo=activo)
    if search:
        qs = qs.filter(models.Q(nombre__icontains=search) | models.Q(codigo__icontains=search))
    return qs


def select_operacion_by_id(operacion_id):
    """Get single Operacion by UUID."""
    from .models import Operacion
    return Operacion.objects.filter(pk=operacion_id).first()


def select_tareas(operacion_id=None, activo: Optional[bool] = None, search: Optional[str] = None):
    """Queryset for listing tareas."""
    from .models import Tarea
    qs = Tarea.objects.select_related('operacion')
    if operacion_id:
        qs = qs.filter(operacion_id=operacion_id)
    if activo is not None:
        qs = qs.filter(activo=activo)
    if search:
        qs = qs.filter(models.Q(nombre__icontains=search) | models.Q(codigo__icontains=search))
    return qs


def select_tarea_by_id(tarea_id):
    """Get single Tarea by UUID."""
    from .models import Tarea
    return Tarea.objects.filter(pk=tarea_id).first()


def select_productos(accion_corto_plazo_id=None, tipo: Optional[str] = None, estado: Optional[str] = None, activo: Optional[bool] = None, search: Optional[str] = None):
    """Queryset for listing productos."""
    from .models import Producto
    qs = Producto.objects.select_related('accion_corto_plazo', 'tipo_producto')
    if accion_corto_plazo_id:
        qs = qs.filter(accion_corto_plazo_id=accion_corto_plazo_id)
    if tipo:
        qs = qs.filter(tipo=tipo)
    if estado:
        qs = qs.filter(estado=estado)
    if activo is not None:
        qs = qs.filter(activo=activo)
    if search:
        qs = qs.filter(models.Q(nombre__icontains=search) | models.Q(codigo__icontains=search))
    return qs


def select_producto_by_id(producto_id):
    """Get single Producto by UUID."""
    from .models import Producto
    return Producto.objects.filter(pk=producto_id).first()


def select_medios_verificacion(indicador_id=None, search: Optional[str] = None):
    """Queryset for listing medios de verificacion."""
    from .models import MedioVerificacion
    qs = MedioVerificacion.objects.select_related('indicador')
    if indicador_id:
        qs = qs.filter(indicador_id=indicador_id)
    if search:
        qs = qs.filter(nombre__icontains=search)
    return qs


def select_medio_verificacion_by_id(medio_id):
    """Get single MedioVerificacion by UUID."""
    from .models import MedioVerificacion
    return MedioVerificacion.objects.filter(pk=medio_id).first()


def select_supuestos(accion_corto_plazo_id=None):
    """Queryset for listing supuestos."""
    from .models import Supuesto
    qs = Supuesto.objects.select_related('accion_corto_plazo')
    if accion_corto_plazo_id:
        qs = qs.filter(accion_corto_plazo_id=accion_corto_plazo_id)
    return qs


def select_supuesto_by_id(supuesto_id):
    """Get single Supuesto by UUID."""
    from .models import Supuesto
    return Supuesto.objects.filter(pk=supuesto_id).first()
