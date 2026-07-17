from django.db import transaction
from django.utils import timezone

from .models import Plan, NodoPlanificacion, PlanVersion, ArticulacionPlanificacion, AccionMedianoPlazo


def crear_pde_sa(codigo, nombre, gestion_inicio, gestion_fin, descripcion=''):
    plan = Plan.objects.create(
        codigo=codigo,
        nombre=nombre,
        tipo='pdes',
        gestion_inicio=gestion_inicio,
        gestion_fin=gestion_fin,
        descripcion=descripcion,
    )
    return plan


def crear_ptdi(codigo, nombre, gestion_inicio, gestion_fin, descripcion=''):
    plan = Plan.objects.create(
        codigo=codigo,
        nombre=nombre,
        tipo='ptdi',
        gestion_inicio=gestion_inicio,
        gestion_fin=gestion_fin,
        descripcion=descripcion,
    )
    return plan


def crear_pei(codigo, nombre, gestion_inicio, gestion_fin, descripcion=''):
    plan = Plan.objects.create(
        codigo=codigo,
        nombre=nombre,
        tipo='pei',
        gestion_inicio=gestion_inicio,
        gestion_fin=gestion_fin,
        descripcion=descripcion,
    )
    return plan


def crear_nodo_planificacion(plan, codigo, nivel, nombre, gestion, padre=None, descripcion='', orden=0):
    nodo = NodoPlanificacion.objects.create(
        plan=plan,
        padre=padre,
        nivel=nivel,
        codigo=codigo,
        nombre=nombre,
        descripcion=descripcion,
        gestion=gestion,
        orden=orden,
    )
    return nodo


def validar_articulacion(nodo_origen_id, nodo_destino_id, gestion):
    errores = []
    if nodo_origen_id == nodo_destino_id:
        errores.append('Un nodo no puede articularse consigo mismo.')
    try:
        nodo_origen = NodoPlanificacion.objects.get(id=nodo_origen_id)
    except NodoPlanificacion.DoesNotExist:
        errores.append(f'El nodo origen {nodo_origen_id} no existe.')
        nodo_origen = None
    try:
        nodo_destino = NodoPlanificacion.objects.get(id=nodo_destino_id)
    except NodoPlanificacion.DoesNotExist:
        errores.append(f'El nodo destino {nodo_destino_id} no existe.')
        nodo_destino = None
    if nodo_origen and nodo_destino:
        if nodo_origen.plan == nodo_destino.plan:
            pass
        existe = ArticulacionPlanificacion.objects.filter(
            nodo_origen_id=nodo_origen_id,
            nodo_destino_id=nodo_destino_id,
            gestion=gestion,
        ).exists()
        if existe:
            errores.append('Ya existe esta articulación para la gestión especificada.')
    return {'valido': len(errores) == 0, 'errores': errores}


@transaction.atomic
def crear_version(plan, version_number, version_name, change_reason, valid_from=None, approved_by=None):
    existing = PlanVersion.objects.filter(plan=plan, version_number=version_number).exists()
    if existing:
        return {
            'exito': False,
            'mensaje': f'Ya existe la versión {version_number} para este plan.',
            'version': None,
        }
    PlanVersion.objects.filter(plan=plan, status='aprobado').update(status='obsoleto')
    version = PlanVersion.objects.create(
        plan=plan,
        version_number=version_number,
        version_name=version_name,
        status='borrador',
        valid_from=valid_from or timezone.now().date(),
        change_reason=change_reason,
    )
    return {'exito': True, 'mensaje': f'Versión {version_number} creada.', 'version': version}


@transaction.atomic
def aprobar_version(version_id, approved_by):
    try:
        version = PlanVersion.objects.get(id=version_id)
    except PlanVersion.DoesNotExist:
        return {'exito': False, 'mensaje': 'La versión no existe.'}
    if version.status == 'aprobado':
        return {'exito': False, 'mensaje': 'La versión ya está aprobada.'}
    if version.status == 'obsoleto':
        return {'exito': False, 'mensaje': 'No se puede aprobar una versión obsoleta.'}
    PlanVersion.objects.filter(
        plan=version.plan, status='aprobado'
    ).update(status='obsoleto')
    version.status = 'aprobado'
    version.approved_at = timezone.now()
    version.approved_by = approved_by
    version.immutable = True
    version.save(update_fields=['status', 'approved_at', 'approved_by', 'immutable', 'updated_at'])
    return {'exito': True, 'mensaje': f'Versión {version.version_number} aprobada.'}


def obtener_nodos_por_plan(plan, nivel=None):
    qs = NodoPlanificacion.objects.filter(plan=plan, activo=True)
    if nivel:
        qs = qs.filter(nivel=nivel)
    return qs.order_by('nivel', 'orden', 'codigo')


def obtener_arbol_nodos(plan):
    raices = NodoPlanificacion.objects.filter(
        plan=plan, padre__isnull=True, activo=True
    ).order_by('orden')

    def _construir(nodo):
        nodo_dict = {
            'id': str(nodo.id),
            'codigo': nodo.codigo,
            'nivel': nodo.nivel,
            'nombre': nodo.nombre,
            'orden': nodo.orden,
            'hijos': [],
        }
        for hijo in NodoPlanificacion.objects.filter(
            padre=nodo, activo=True
        ).order_by('orden'):
            nodo_dict['hijos'].append(_construir(hijo))
        return nodo_dict

    return [_construir(r) for r in raices]


def crear_accion_mediano_plazo(codigo, nombre, nodo_planificacion, gestion_inicio, gestion_fin, responsable=None, descripcion=''):
    accion = AccionMedianoPlazo.objects.create(
        codigo=codigo,
        nombre=nombre,
        descripcion=descripcion,
        nodo_planificacion=nodo_planificacion,
        gestion_inicio=gestion_inicio,
        gestion_fin=gestion_fin,
        responsable=responsable,
    )
    return accion


def crear_accion_corto_plazo(codigo, nombre, accion_mediano_plazo, unidad_responsable, gestion, fecha_inicio=None, fecha_fin=None, descripcion='', justificacion=''):
    from .models import AccionCortoPlazo
    accion = AccionCortoPlazo.objects.create(
        codigo=codigo,
        nombre=nombre,
        descripcion=descripcion,
        justificacion=justificacion,
        accion_mediano_plazo=accion_mediano_plazo,
        unidad_responsable=unidad_responsable,
        gestion=gestion,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
    )
    return accion
