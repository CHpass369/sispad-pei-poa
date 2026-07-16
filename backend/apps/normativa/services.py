"""
Servicios de evaluación de reglas presupuestarias legales.

Las reglas se evalúan mediante métodos tipados (no eval dinámico).
Cada regla tiene una estrategia de cálculo implementada como función.
"""
from decimal import Decimal
from typing import Any
from .models import ReglaPresupuestariaLegal


def _evaluar_limite_gasto_funcionamiento(params: dict, data: dict) -> dict:
    """Regla 1: Gastos de funcionamiento no pueden superar el límite legal."""
    presupuesto_total = Decimal(str(data.get('presupuesto_total', 0)))
    gasto_funcionamiento = Decimal(str(data.get('gasto_funcionamiento', 0)))
    porcentaje_limite = Decimal(str(params.get('porcentaje', 0.60)))
    maximo_permitido = presupuesto_total * porcentaje_limite
    return {
        'cumple': gasto_funcionamiento <= maximo_permitido,
        'valor_actual': float(gasto_funcionamiento),
        'limite': float(maximo_permitido),
        'diferencia': float(maximo_permitido - gasto_funcionamiento),
    }


def _evaluar_no_superar_techo(params: dict, data: dict) -> dict:
    """Regla 2: El monto formulado no puede superar el techo asignado."""
    techo = Decimal(str(data.get('techo_asignado', 0)))
    formulado = Decimal(str(data.get('monto_formulado', 0)))
    return {
        'cumple': formulado <= techo,
        'valor_actual': float(formulado),
        'limite': float(techo),
        'diferencia': float(techo - formulado),
    }


def _evaluar_consistencia_anual_plurianual(params: dict, data: dict) -> dict:
    """Regla 3: El presupuesto anual debe ser consistente con el plurianual."""
    anual = Decimal(str(data.get('presupuesto_anual', 0)))
    plurianual = Decimal(str(data.get('presupuesto_plurianual', 0)))
    tolerancia = Decimal(str(params.get('tolerancia', 0.05)))
    if plurianual > 0:
        diff = abs(anual - plurianual) / plurianual
        cumple = diff <= tolerancia
    else:
        cumple = anual == 0
    return {
        'cumple': cumple,
        'valor_actual': float(anual),
        'plurianual': float(plurianual),
        'diferencia_porcentual': float(diff) if plurianual > 0 else 0,
    }


def _evaluar_gasto_sus(params: dict, data: dict) -> dict:
    """Regla: Asignación obligatoria SUS."""
    presupuesto = Decimal(str(data.get('presupuesto_total', 0)))
    asignado = Decimal(str(data.get('asignacion_sus', 0)))
    minimo = Decimal(str(params.get('porcentaje', 0.10))) * presupuesto
    return {
        'cumple': asignado >= minimo,
        'valor_actual': float(asignado),
        'minimo_requerido': float(minimo),
    }


def _evaluar_renta_dignidad(params: dict, data: dict) -> dict:
    """Regla: Asignación obligatoria Renta Dignidad."""
    presupuesto = Decimal(str(data.get('presupuesto_total', 0)))
    asignado = Decimal(str(data.get('asignacion_renta_dignidad', 0)))
    minimo = Decimal(str(params.get('porcentaje', 0.0075))) * presupuesto
    return {
        'cumple': asignado >= minimo,
        'valor_actual': float(asignado),
        'minimo_requerido': float(minimo),
    }


def _evaluar_seguridad_ciudadana(params: dict, data: dict) -> dict:
    """Regla: Asignación obligatoria Seguridad Ciudadana."""
    presupuesto = Decimal(str(data.get('presupuesto_total', 0)))
    asignado = Decimal(str(data.get('asignacion_seguridad', 0)))
    minimo = Decimal(str(params.get('porcentaje', 0.10))) * presupuesto
    return {
        'cumple': asignado >= minimo,
        'valor_actual': float(asignado),
        'minimo_requerido': float(minimo),
    }


STRATEGY_MAP = {
    'limite_gasto_funcionamiento': _evaluar_limite_gasto_funcionamiento,
    'no_superar_techo': _evaluar_no_superar_techo,
    'consistencia_anual_plurianual': _evaluar_consistencia_anual_plurianual,
    'gasto_sus': _evaluar_gasto_sus,
    'renta_dignidad': _evaluar_renta_dignidad,
    'seguridad_ciudadana': _evaluar_seguridad_ciudadana,
}


def evaluar_reglas_presupuestarias(gestion: int, data: dict) -> list[dict]:
    """
    Evalúa todas las reglas activas aplicables a una gestión.

    Args:
        gestion: Año de gestión
        data: Diccionario con datos presupuestarios a evaluar

    Returns:
        Lista de resultados con estado, mensaje y detalle por regla
    """
    reglas = ReglaPresupuestariaLegal.objects.filter(
        activo=True,
        gestion_desde__lte=gestion,
    ).exclude(gestion_hasta__lt=gestion) | ReglaPresupuestariaLegal.objects.filter(
        activo=True,
        gestion_desde__lte=gestion,
        gestion_hasta__isnull=True,
    )

    resultados = []
    for regla in reglas:
        estrategia = STRATEGY_MAP.get(regla.codigo)
        if not estrategia:
            resultados.append({
                'regla': regla.codigo,
                'nombre': regla.nombre,
                'severidad': regla.severidad,
                'cumple': None,
                'error': f'Sin implementación: {regla.codigo}',
            })
            continue

        try:
            params = regla.parametros or {}
            evaluacion = estrategia(params, data)
            cumple = evaluacion.pop('cumple', False)

            resultados.append({
                'regla': regla.codigo,
                'nombre': regla.nombre,
                'severidad': regla.severidad,
                'mensaje': regla.mensaje if not cumple else '',
                'cumple': cumple,
                'detalle': evaluacion,
            })
        except Exception as e:
            resultados.append({
                'regla': regla.codigo,
                'nombre': regla.nombre,
                'severidad': regla.severidad,
                'cumple': None,
                'error': str(e),
            })

    return resultados
