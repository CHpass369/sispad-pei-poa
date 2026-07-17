from django.db import transaction

from .models import UnidadOrganizacional, UnidadEjecutora, DireccionAdministrativa, AsignacionUsuarioUnidad


def crear_estructura(gestion, unidades_data, da_data=None):
    resultado = {'da': None, 'unidades': []}

    if da_data:
        da, _ = DireccionAdministrativa.objects.get_or_create(
            codigo=da_data['codigo'],
            gestion=gestion,
            defaults={
                'nombre': da_data['nombre'],
                'responsable': da_data.get('responsable'),
            },
        )
        resultado['da'] = da

    for ud in unidades_data:
        padre_id = ud.get('padre_id')
        padre = None
        if padre_id:
            try:
                padre = UnidadOrganizacional.objects.get(id=padre_id, gestion=gestion)
            except UnidadOrganizacional.DoesNotExist:
                pass
        unidad, created = UnidadOrganizacional.objects.update_or_create(
            codigo=ud['codigo'],
            gestion=gestion,
            defaults={
                'nombre': ud['nombre'],
                'sigla': ud.get('sigla', ''),
                'tipo_id': ud['tipo_id'],
                'padre': padre,
                'responsable': ud.get('responsable'),
                'orden': ud.get('orden', 0),
            },
        )
        resultado['unidades'].append(unidad)

    return resultado


def obtener_unidades_por_padre(padre_id=None, gestion=None):
    qs = UnidadOrganizacional.objects.filter(activo=True)
    if gestion:
        qs = qs.filter(gestion=gestion)
    if padre_id:
        qs = qs.filter(padre_id=padre_id)
    else:
        qs = qs.filter(padre__isnull=True)
    return qs.select_related('tipo', 'padre', 'responsable').order_by('orden')


def obtener_arbol_completo(gestion):
    raices = UnidadOrganizacional.objects.filter(
        gestion=gestion, padre__isnull=True, activo=True
    ).select_related('tipo', 'responsable').order_by('orden')

    def _construir_arbol(unidad):
        nodo = {
            'id': str(unidad.id),
            'codigo': unidad.codigo,
            'nombre': unidad.nombre,
            'sigla': unidad.sigla,
            'tipo': str(unidad.tipo),
            'responsable': str(unidad.responsable) if unidad.responsable else None,
            'hijos': [],
        }
        hijos = UnidadOrganizacional.objects.filter(
            padre=unidad, activo=True
        ).select_related('tipo', 'responsable').order_by('orden')
        for hijo in hijos:
            nodo['hijos'].append(_construir_arbol(hijo))
        return nodo

    arbol = []
    for raiz in raices:
        arbol.append(_construir_arbol(raiz))
    return arbol


def validar_dependencia_jerarquica(unidad_id, padre_id):
    if unidad_id == padre_id:
        return {
            'valido': False,
            'mensaje': 'Una unidad no puede ser su propio padre.',
        }
    try:
        unidad = UnidadOrganizacional.objects.get(id=unidad_id)
    except UnidadOrganizacional.DoesNotExist:
        return {
            'valido': False,
            'mensaje': f'La unidad {unidad_id} no existe.',
        }
    actual = UnidadOrganizacional.objects.filter(id=padre_id).first()
    visitados = {unidad_id}
    while actual is not None:
        if str(actual.pk) in visitados:
            return {
                'valido': False,
                'mensaje': 'Se detectó un ciclo en la jerarquía organizacional.',
            }
        visitados.add(str(actual.pk))
        actual = actual.padre
    return {'valido': True, 'mensaje': 'Dependencia jerárquica válida.'}


def asignar_usuario_unidad(usuario, unidad, gestion, es_responsable_poa=False):
    asignacion, created = AsignacionUsuarioUnidad.objects.update_or_create(
        usuario=usuario,
        unidad=unidad,
        gestion=gestion,
        defaults={
            'es_responsable_poa': es_responsable_poa,
            'activo': True,
        },
    )
    return asignacion


def obtener_unidades_ejecutoras(gestion=None, da_id=None):
    qs = UnidadEjecutora.objects.filter(activo=True)
    if gestion:
        qs = qs.filter(gestion=gestion)
    if da_id:
        qs = qs.filter(da_id=da_id)
    return qs.select_related('da', 'responsable').order_by('da__codigo', 'codigo')
