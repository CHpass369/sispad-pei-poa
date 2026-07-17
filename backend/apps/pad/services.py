from decimal import Decimal
from django.db import transaction
from django.db.models import Sum

from .models import (
    SectorPAD, PoliticaPAD, LineamientoEstrategico,
    ResultadoTerritorial, ProductoTerritorial, ProgramacionAnualPAD,
)


@transaction.atomic
def crear_sector(codigo, nombre):
    sector, _ = SectorPAD.objects.update_or_create(
        codigo=codigo,
        defaults={'nombre': nombre},
    )
    return sector


@transaction.atomic
def crear_politica(codigo, nombre, gestion, descripcion=''):
    politica, _ = PoliticaPAD.objects.update_or_create(
        codigo=codigo,
        gestion=gestion,
        defaults={'nombre': nombre, 'descripcion': descripcion},
    )
    return politica


@transaction.atomic
def crear_lineamiento(codigo, nombre, politica_id, gestion):
    lineamiento, _ = LineamientoEstrategico.objects.update_or_create(
        codigo=codigo,
        politica_id=politica_id,
        gestion=gestion,
        defaults={'nombre': nombre},
    )
    return lineamiento


@transaction.atomic
def crear_resultado(codigo, nombre, lineamiento_id, gestion, sector_id=None, indicador='', formula='', linea_base=None, meta_2030=None):
    resultado, created = ResultadoTerritorial.objects.update_or_create(
        codigo=codigo,
        lineamiento_id=lineamiento_id,
        gestion=gestion,
        defaults={
            'nombre': nombre,
            'sector_id': sector_id,
            'indicador': indicador,
            'formula': formula,
            'linea_base': linea_base,
            'meta_2030': meta_2030,
        },
    )
    return resultado


@transaction.atomic
def crear_producto(codigo, nombre, resultado_id, gestion, **kwargs):
    producto, created = ProductoTerritorial.objects.update_or_create(
        codigo=codigo,
        resultado_id=resultado_id,
        gestion=gestion,
        defaults={
            'nombre': nombre,
            'territorializacion': kwargs.get('territorializacion', ''),
            'responsable': kwargs.get('responsable', ''),
            'indicador': kwargs.get('indicador', ''),
            'formula': kwargs.get('formula', ''),
            'linea_base': kwargs.get('linea_base'),
            'meta_2030': kwargs.get('meta_2030'),
            'cuenta_con_financiamiento': kwargs.get('cuenta_con_financiamiento', 'NO'),
            'presupuesto_total_pad': kwargs.get('presupuesto_total_pad'),
        },
    )
    return producto


def validar_programacion_presupuestaria(resultado_id=None, producto_id=None):
    errores = []
    if resultado_id:
        programaciones = ProgramacionAnualPAD.objects.filter(
            resultado_id=resultado_id, tipo='financiera'
        )
        total_financiero = programaciones.aggregate(
            total=Sum('valor')
        )['total'] or Decimal('0')
        productos = ProductoTerritorial.objects.filter(resultado_id=resultado_id)
        total_presupuesto = Decimal('0')
        for p in productos:
            if p.presupuesto_total_pad:
                total_presupuesto += p.presupuesto_total_pad
        if total_financiero > 0 and total_presupuesto > 0 and total_financiero != total_presupuesto:
            errores.append(
                'La programacion financiera (Bs '
                + str(total_financiero)
                + ') no coincide con el presupuesto total (Bs '
                + str(total_presupuesto)
                + ').'
            )
    if producto_id:
        programaciones = ProgramacionAnualPAD.objects.filter(
            producto_id=producto_id, tipo='financiera'
        )
        if not programaciones.exists():
            errores.append('El producto no tiene programacion financiera.')
    return {'valido': len(errores) == 0, 'errores': errores}


def calcular_total_programacion(resultado_id=None, producto_id=None, anio=None, tipo='financiera'):
    qs = ProgramacionAnualPAD.objects.filter(tipo=tipo)
    if resultado_id:
        qs = qs.filter(resultado_id=resultado_id)
    if producto_id:
        qs = qs.filter(producto_id=producto_id)
    if anio:
        qs = qs.filter(anio=anio)
    total = qs.aggregate(total=Sum('valor'))['total'] or Decimal('0')
    return {
        'total': total,
        'tipo': tipo,
        'anio': anio,
        'resultado_id': resultado_id,
        'producto_id': producto_id,
    }


def obtener_arbol_pad(gestion):
    from .models import PoliticaPAD
    politicas = PoliticaPAD.objects.filter(gestion=gestion).order_by('codigo')
    arbol = []
    for politica in politicas:
        nodo_politica = {
            'id': str(politica.id),
            'codigo': politica.codigo,
            'nombre': politica.nombre,
            'tipo': 'politica',
            'hijos': [],
        }
        lineamientos = LineamientoEstrategico.objects.filter(
            politica=politica, gestion=gestion
        ).order_by('codigo')
        for lin in lineamientos:
            nodo_lin = {
                'id': str(lin.id),
                'codigo': lin.codigo,
                'nombre': lin.nombre,
                'tipo': 'lineamiento',
                'hijos': [],
            }
            resultados = ResultadoTerritorial.objects.filter(
                lineamiento=lin, gestion=gestion
            ).order_by('codigo')
            for res in resultados:
                nodo_res = {
                    'id': str(res.id),
                    'codigo': res.codigo,
                    'nombre': res.nombre,
                    'tipo': 'resultado',
                    'hijos': [],
                }
                productos = ProductoTerritorial.objects.filter(
                    resultado=res, gestion=gestion
                ).order_by('codigo')
                for prod in productos:
                    nodo_res['hijos'].append({
                        'id': str(prod.id),
                        'codigo': prod.codigo,
                        'nombre': prod.nombre,
                        'tipo': 'producto',
                    })
                nodo_lin['hijos'].append(nodo_res)
            nodo_politica['hijos'].append(nodo_lin)
        arbol.append(nodo_politica)
    return arbol
