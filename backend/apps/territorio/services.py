from decimal import Decimal

from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D

from .models import Distrito, UnidadTerritorial, LocalizacionTerritorial


def obtener_geometria(entidad, entidad_id):
    localizacion = LocalizacionTerritorial.objects.filter(
        entidad=entidad, entidad_id=str(entidad_id), activo=True
    ).first()
    if localizacion is None:
        return None
    return {
        'id': str(localizacion.id),
        'geometria': localizacion.geometria,
        'geometria_4326': localizacion.geometria_4326,
        'distrito': str(localizacion.distrito) if localizacion.distrito else None,
        'unidad_territorial': str(localizacion.unidad_territorial) if localizacion.unidad_territorial else None,
        'direccion_referencia': localizacion.direccion_referencia,
    }


def calcular_area(localizacion_id):
    try:
        localizacion = LocalizacionTerritorial.objects.get(id=localizacion_id)
    except LocalizacionTerritorial.DoesNotExist:
        return None
    geom = localizacion.geometria or localizacion.geometria_4326
    if geom is None:
        return {'area_ha': Decimal('0'), 'area_m2': Decimal('0')}
    try:
        if geom.srid != 32719:
            geom_32719 = geom.clone()
            geom_32719.transform(32719)
        else:
            geom_32719 = geom
        area_m2 = Decimal(str(geom_32719.area))
        area_ha = (area_m2 / Decimal('10000')).quantize(Decimal('0.0001'))
        return {'area_ha': area_ha, 'area_m2': area_m2}
    except Exception:
        return {'area_ha': Decimal('0'), 'area_m2': Decimal('0')}


def validar_intersect(geom_a, geom_b):
    if geom_a is None or geom_b is None:
        return {'intersecta': False, 'mensaje': 'Geometria nula.'}
    try:
        intersecta = geom_a.intersects(geom_b)
        return {
            'intersecta': intersecta,
            'mensaje': 'Las geometrias se intersectan.' if intersecta else 'Las geometrias no se intersectan.',
        }
    except Exception as e:
        return {'intersecta': False, 'mensaje': 'Error al evaluar interseccion: ' + str(e)}


def buscar_por_punto(lat, lng, srid=4326):
    punto = Point(float(lng), float(lat), srid=srid)
    if srid != 4326:
        punto.transform(4326)
    distritos = Distrito.objects.filter(geometria__contains=punto)
    unidades = UnidadTerritorial.objects.filter(geometria__contains=punto)
    return {
        'distritos': [
            {'id': str(d.id), 'codigo': d.codigo, 'nombre': d.nombre}
            for d in distritos
        ],
        'unidades_territoriales': [
            {'id': str(u.id), 'codigo': u.codigo, 'nombre': u.nombre, 'tipo': u.tipo}
            for u in unidades
        ],
    }


def crear_localizacion(entidad, entidad_id, geometria, gestion, distrito_id=None, unidad_territorial_id=None, direccion_referencia=''):
    localizacion = LocalizacionTerritorial.objects.create(
        entidad=entidad,
        entidad_id=str(entidad_id),
        geometria=geometria,
        distrito_id=distrito_id,
        unidad_territorial_id=unidad_territorial_id,
        direccion_referencia=direccion_referencia,
        gestion=gestion,
    )
    return localizacion


def obtener_distritos():
    return Distrito.objects.all().order_by('codigo')


def obtener_unidades_territoriales(distrito_id=None, tipo=None):
    qs = UnidadTerritorial.objects.all()
    if distrito_id:
        qs = qs.filter(distrito_id=distrito_id)
    if tipo:
        qs = qs.filter(tipo=tipo)
    return qs.select_related('distrito').order_by('distrito__codigo', 'tipo', 'nombre')
