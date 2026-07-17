from decimal import Decimal, InvalidOperation
from django.db.models import Sum, F

from .models import Indicador, MetaProgramada


def calcular_avance_indicador(indicador, gestion):
    meta = MetaProgramada.objects.filter(
        indicador=indicador, gestion=gestion
    ).order_by('-version').first()
    if meta is None or meta.meta_anual == 0:
        return {
            'avance': Decimal('0'),
            'meta_anual': Decimal('0'),
            'porcentaje': Decimal('0'),
        }
    from apps.poau.models import EjecucionFisica, POAUActividad
    total_ejecutado = EjecucionFisica.objects.filter(
        actividad__accion_corto_plazo__operaciones__isnull=False,
    ).aggregate(total=Sum('ejecutado'))['total'] or Decimal('0')
    porcentaje = (total_ejecutado / meta.meta_anual * 100).quantize(Decimal('0.01')) if meta.meta_anual else Decimal('0')
    return {
        'avance': total_ejecutado,
        'meta_anual': meta.meta_anual,
        'porcentaje': porcentaje,
    }


def obtener_meta_por_gestion(indicador, gestion):
    return MetaProgramada.objects.filter(
        indicador=indicador, gestion=gestion
    ).order_by('-version').first()


def validar_formula(indicador):
    formula = indicador.formula
    if not formula:
        return {'valido': False, 'mensaje': 'El indicador no tiene fórmula definida.'}
    formula = formula.strip()
    if not formula:
        return {'valido': False, 'mensaje': 'La fórmula está vacía.'}
    caracteres_permitidos = set('0123456789+-*/() .,variable_')
    for char in formula.lower():
        if char not in caracteres_permitidos:
            if char.isalpha():
                continue
            return {
                'valido': False,
                'mensaje': f'La fórmula contiene caracteres no permitidos: "{char}".',
            }
    return {'valido': True, 'mensaje': 'Fórmula válida.'}


def registrar_resultado_medicion(indicador, gestion, valor, trimestre=None, observaciones=''):
    meta = MetaProgramada.objects.filter(
        indicador=indicador, gestion=gestion
    ).order_by('-version').first()
    if meta is None:
        meta = MetaProgramada.objects.create(
            indicador=indicador,
            gestion=gestion,
            meta_anual=Decimal('0'),
            version=1,
        )
    trimestre_map = {
        1: 'trimestre1', 2: 'trimestre2',
        3: 'trimestre3', 4: 'trimestre4',
    }
    if trimestre and trimestre in trimestre_map:
        setattr(meta, trimestre_map[trimestre], Decimal(str(valor)))
    meta.observaciones = observaciones
    meta.save()
    return meta


def calcular_tendencia(indicador, gestiones=None):
    if gestiones is None:
        from django.utils import timezone
        anio_actual = timezone.now().year
        gestiones = range(anio_actual - 3, anio_actual + 1)
    metas = []
    for g in gestiones:
        meta = MetaProgramada.objects.filter(
            indicador=indicador, gestion=g
        ).order_by('-version').first()
        if meta:
            metas.append({
                'gestion': g,
                'meta_anual': meta.meta_anual,
                'trimestre1': meta.trimestre1,
                'trimestre2': meta.trimestre2,
                'trimestre3': meta.trimestre3,
                'trimestre4': meta.trimestre4,
            })
    if len(metas) < 2:
        return {'tendencia': 'sin_datos', 'metas': metas}
    valores = [m['meta_anual'] for m in metas]
    tendencia = 'estable'
    if valores[-1] > valores[0]:
        tendencia = 'creciente'
    elif valores[-1] < valores[0]:
        tendencia = 'decreciente'
    return {'tendencia': tendencia, 'metas': metas}


def crear_indicador(codigo, nombre, tipo_comportamiento='acumulable', **kwargs):
    indicador = Indicador.objects.create(
        codigo=codigo,
        nombre=nombre,
        tipo_comportamiento=tipo_comportamiento,
        **kwargs,
    )
    return indicador


def calcular_avance_por_indicador(indicador_id, gestion):
    try:
        indicador = Indicador.objects.get(id=indicador_id)
    except Indicador.DoesNotExist:
        return None
    return calcular_avance_indicador(indicador, gestion)
