from django.db.models import Q


def validar_codigo_unico_unidad(codigo, gestion, exclude_id=None):
    from apps.organizacion.models import UnidadOrganizacional
    qs = UnidadOrganizacional.objects.filter(codigo=codigo, gestion=gestion)
    if exclude_id:
        qs = qs.exclude(id=exclude_id)
    if qs.exists():
        return {
            'valido': False,
            'mensaje': 'Ya existe una unidad con codigo "' + codigo + '" en la gestion ' + str(gestion) + '.',
        }
    return {'valido': True, 'mensaje': 'Codigo unico.'}


def validar_unidad_con_hijos(unidad_id):
    from apps.organizacion.models import UnidadOrganizacional
    try:
        unidad = UnidadOrganizacional.objects.get(id=unidad_id)
    except UnidadOrganizacional.DoesNotExist:
        return {'valido': False, 'mensaje': 'Unidad no encontrada.'}
    hijos = UnidadOrganizacional.objects.filter(padre=unidad, activo=True).count()
    return {
        'valido': True,
        'mensaje': 'Unidad tiene ' + str(hijos) + ' unidades hijas.',
        'tiene_hijos': hijos > 0,
        'total_hijos': hijos,
    }


def validar_estructura_completa(gestion):
    from apps.organizacion.models import UnidadOrganizacional
    unidades = UnidadOrganizacional.objects.filter(gestion=gestion, activo=True)
    if not unidades.exists():
        return {'valido': False, 'mensaje': 'No hay unidades registradas para la gestion ' + str(gestion) + '.'}
    sin_padre = unidades.filter(padre__isnull=True)
    if sin_padre.count() > 1:
        return {
            'valido': False,
            'mensaje': 'Hay ' + str(sin_padre.count()) + ' unidades raiz. Debe haber exactamente una.',
        }
    return {'valido': True, 'mensaje': 'Estructura organizacional completa.'}
