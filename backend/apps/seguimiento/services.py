from decimal import Decimal, InvalidOperation
from django.db.models import Sum, Count, Q, Avg, F
from django.utils import timezone

from .models import (
    EntradaSeguimiento, Alerta, UmbralConfiguracion, ReporteSeguimiento,
)


def _safe_divide(numerator, denominator):
    """Division segura que retorna Decimal(0) si el denominador es cero."""
    try:
        if denominator is None or denominator == 0:
            return Decimal('0')
        return Decimal(str(numerator)) / Decimal(str(denominator))
    except (InvalidOperation, TypeError, ValueError):
        return Decimal('0')


def _safe_decimal(value, default=Decimal('0')):
    """Convierte un valor a Decimal de forma segura."""
    if value is None:
        return default
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return default


def calcular_eficacia_fisica(entry):
    """Retorna el porcentaje de eficacia fisica (ejecutado vs programado)."""
    programado = _safe_decimal(entry.programado_fisico)
    ejecutado = _safe_decimal(entry.ejecutado_fisico)
    return _safe_divide(ejecutado, programado) * Decimal('100')


def calcular_ejecucion_financiera(entry):
    """Retorna el porcentaje de ejecucion financiera."""
    programado = _safe_decimal(entry.programado_financiero)
    ejecutado = _safe_decimal(entry.ejecutado_financiero)
    return _safe_divide(ejecutado, programado) * Decimal('100')


def calcular_eficiencia(entry):
    """Retorna la eficiencia: relacion entre avance fisico y financiero.

    Si ambos son 0, retorna 0. Si el financiero es mayor que el fisico,
    indica sobre-ejecucion financiera (eficiencia > 100%).
    """
    avance_fisico = _safe_decimal(entry.porcentaje_avance_fisico)
    avance_financiero = _safe_decimal(entry.porcentaje_avance_financiero)
    if avance_financiero == 0:
        return Decimal('0')
    return _safe_divide(avance_fisico, avance_financiero) * Decimal('100')


def calcular_desviacion(entry):
    """Retorna la desviacion porcentual entre programado y ejecutado.

    Desviacion = ((ejecutado - programado) / programado) * 100
    """
    programado_fisico = _safe_decimal(entry.programado_fisico)
    ejecutado_fisico = _safe_decimal(entry.ejecutado_fisico)
    if programado_fisico == 0:
        return Decimal('0')
    return _safe_divide(
        ejecutado_fisico - programado_fisico, programado_fisico
    ) * Decimal('100')


def calcular_proyeccion_cierre(entry):
    """Proyecta el avance a fin de gestion basado en la tendencia actual.

    Asume distribucion lineal del esfuerzo en el tiempo.
    Retorna un diccionario con proyeccion_fisica y proyeccion_financiera.
    """
    ahora = timezone.now()
    inicio_anio = timezone.datetime(ahora.year, 1, 1, tzinfo=timezone.utc)
    dias_transcurridos = max((ahora - inicio_anio).days, 1)
    dias_totales = 365
    factor_proyeccion = Decimal(str(dias_totales / dias_transcurridos))

    avance_fisico = _safe_decimal(entry.porcentaje_avance_fisico)
    avance_financiero = _safe_decimal(entry.porcentaje_avance_financiero)

    proyeccion_fisica = min(avance_fisico * factor_proyeccion, Decimal('100'))
    proyeccion_financiera = min(
        avance_financiero * factor_proyeccion, Decimal('100')
    )

    return {
        'proyeccion_fisica': round(proyeccion_fisica, 2),
        'proyeccion_financiera': round(proyeccion_financiera, 2),
        'dias_transcurridos': dias_transcurridos,
        'dias_totales': dias_totales,
    }


def determinar_semaforo(percentage):
    """Retorna el color del semaforo basado en el porcentaje.

    Verde: >= 80%
    Amarillo: 50% - 79%
    Rojo: < 50%
    """
    p = _safe_decimal(percentage)
    if p >= Decimal('80'):
        return 'verde'
    elif p >= Decimal('50'):
        return 'amarillo'
    return 'rojo'


def obtener_umbrales():
    """Retorna los umbrales activos como diccionario."""
    umbrales = UmbralConfiguracion.objects.filter(activo=True)
    return {
        u.tipo_umbral: {
            'porcentaje_minimo': u.porcentaje_minimo,
            'porcentaje_maximo': u.porcentaje_maximo,
            'descripcion': u.descripcion,
        }
        for u in umbrales
    }


def generar_alertas(gestion, periodo=None):
    """Escanea las entradas de seguimiento y genera alertas segun umbrales.

    Retorna el numero de alertas generadas.
    """
    umbrales = obtener_umbrales()
    entradas_qs = EntradaSeguimiento.objects.filter(
        reporte__gestion=gestion,
    ).select_related('actividad', 'reporte')

    if periodo:
        entradas_qs = entradas_qs.filter(reporte__periodo=periodo)

    alertas_generadas = 0

    for entry in entradas_qs:
        nuevas_alertas = _evaluar_entradas(entry, umbrales)
        alertas_generadas += len(nuevas_alertas)

    return alertas_generadas


def _evaluar_entradas(entry, umbrales):
    """Evalua una entrada individual contra los umbrales y crea alertas."""
    ahora = timezone.now()
    entradas_creadas = []

    avance_fisico = _safe_decimal(entry.porcentaje_avance_fisico)
    avance_financiero = _safe_decimal(entry.porcentaje_avance_financiero)
    programado_fisico = _safe_decimal(entry.programado_fisico)
    programado_financiero = _safe_decimal(entry.programado_financiero)
    ejecutado_fisico = _safe_decimal(entry.ejecutado_fisico)
    ejecutado_financiero = _safe_decimal(entry.ejecutado_financiero)
    presupuesto_inicial = _safe_decimal(entry.presupuesto_inicial)
    actividad = entry.actividad

    # Ejecucion fisica baja
    umbral = umbrales.get('ejecucion_fisica_baja')
    if umbral and avance_fisico < umbral['porcentaje_minimo']:
        entradas_creadas.append(_crear_alerta(
            entry=entry,
            tipo='ejecucion_fisica_baja',
            severidad=_determinar_severidad(avance_fisico, umbral),
            mensaje=(
                f'Avance fisico {avance_fisico}% por debajo del umbral '
                f'minimo {umbral["porcentaje_minimo"]}%'
            ),
            fecha=ahora,
        ))

    # Ejecucion financiera baja
    umbral = umbrales.get('ejecucion_financiera_baja')
    if umbral and avance_financiero < umbral['porcentaje_minimo']:
        entradas_creadas.append(_crear_alerta(
            entry=entry,
            tipo='ejecucion_financiera_baja',
            severidad=_determinar_severidad(avance_financiero, umbral),
            mensaje=(
                f'Ejecucion financiera {avance_financiero}% por debajo del '
                f'umbral minimo {umbral["porcentaje_minimo"]}%'
            ),
            fecha=ahora,
        ))

    # Avance sin financiera
    if (avance_fisico > Decimal('0') and programado_financiero == 0
            and presupuesto_inicial == 0):
        entradas_creadas.append(_crear_alerta(
            entry=entry,
            tipo='avance_sin_financiera',
            severidad='moderada',
            mensaje=(
                f'Actividad "{actividad.nombre[:80]}" tiene avance fisico '
                f'de {avance_fisico}% sin programacion financiera'
            ),
            fecha=ahora,
        ))

    # Financiera sin avance
    if avance_financiero > Decimal('0') and avance_fisico == 0:
        entradas_creadas.append(_crear_alerta(
            entry=entry,
            tipo='financiera_sin_avance',
            severidad='moderada',
            mensaje=(
                f'Actividad "{actividad.nombre[:80]}" tiene ejecucion '
                f'financiera de {avance_financiero}% sin avance fisico'
            ),
            fecha=ahora,
        ))

    # Sobreejecucion
    if (programado_fisico > 0 and ejecutado_fisico > programado_fisico):
        porcentaje_sobre = _safe_divide(
            ejecutado_fisico - programado_fisico, programado_fisico
        ) * Decimal('100')
        entradas_creadas.append(_crear_alerta(
            entry=entry,
            tipo='sobreejecucion',
            severidad='grave',
            mensaje=(
                f'Sobreejecucion fisica del {porcentaje_sobre}% '
                f'(ejecutado: {ejecutado_fisico}, programado: {programado_fisico})'
            ),
            fecha=ahora,
        ))

    if (programado_financiero > 0 and ejecutado_financiero > programado_financiero):
        porcentaje_sobre = _safe_divide(
            ejecutado_financiero - programado_financiero, programado_financiero
        ) * Decimal('100')
        entradas_creadas.append(_crear_alerta(
            entry=entry,
            tipo='sobreejecucion',
            severidad='grave',
            mensaje=(
                f'Sobreejecucion financiera del {porcentaje_sobre}% '
                f'(ejecutado: {ejecutado_financiero}, '
                f'programado: {programado_financiero})'
            ),
            fecha=ahora,
        ))

    # Sin evidencia
    if (avance_fisico > Decimal('0') and not entry.evidencia.strip()):
        entradas_creadas.append(_crear_alerta(
            entry=entry,
            tipo='sin_evidencia',
            severidad='leve',
            mensaje=(
                f'Actividad "{actividad.nombre[:80]}" tiene avance '
                f'sin evidencia registrada'
            ),
            fecha=ahora,
        ))

    # Incumplimiento de accion correctiva
    if entry.accion_correctiva and avance_fisico < Decimal('50'):
        entradas_creadas.append(_crear_alerta(
            entry=entry,
            tipo='incumplimiento_correctivo',
            severidad='moderada',
            mensaje=(
                f'Accion correctiva definida pero avance fisico '
                f'solo {avance_fisico}%'
            ),
            fecha=ahora,
        ))

    return entradas_creadas


def _crear_alerta(entry, tipo, severidad, mensaje, fecha):
    """Crea una alerta si no existe una activa del mismo tipo."""
    if not Alerta.objects.filter(
        entrada=entry, tipo=tipo, activa=True
    ).exists():
        return Alerta.objects.create(
            entrada=entry,
            tipo=tipo,
            severidad=severidad,
            mensaje=mensaje,
            activa=True,
            creado_at=fecha,
        )
    return None


def _determinar_severidad(porcentaje, umbral):
    """Determina la severidad basada en que tan lejos esta del umbral."""
    minimo = _safe_decimal(umbral['porcentaje_minimo'])
    if porcentaje < minimo / Decimal('2'):
        return 'grave'
    elif porcentaje < minimo * Decimal('0.8'):
        return 'moderada'
    return 'leve'


def dashboard_seguimiento(gestion):
    """Retorna datos agregados del dashboard de seguimiento.

    Incluye: conteo por semaforo, alertas activas, progreso promedio
    y detalle por unidad organizacional.
    """
    entradas = EntradaSeguimiento.objects.filter(
        reporte__gestion=gestion,
    ).select_related('actividad', 'reporte', 'reporte__unidad_organizacional')

    total = entradas.count()
    if total == 0:
        return _dashboard_vacio(gestion)

    verde = 0
    amarillo = 0
    rojo = 0

    for entry in entradas:
        semaforo = determinar_semaforo(entry.porcentaje_avance_fisico)
        if semaforo == 'verde':
            verde += 1
        elif semaforo == 'amarillo':
            amarillo += 1
        else:
            rojo += 1

    promedio_fisico = entradas.aggregate(
        avg=Avg('porcentaje_avance_fisico')
    )['avg'] or Decimal('0')
    promedio_financiero = entradas.aggregate(
        avg=Avg('porcentaje_avance_financiero')
    )['avg'] or Decimal('0')

    alertas_activas = Alerta.objects.filter(
        entrada__reporte__gestion=gestion, activa=True
    ).count()

    alertas_por_tipo = (
        Alerta.objects.filter(
            entrada__reporte__gestion=gestion, activa=True
        )
        .values('tipo')
        .annotate(cantidad=Count('id'))
        .order_by('-cantidad')
    )

    unidades_consolidado = (
        entradas.values(
            'reporte__unidad_organizacional__codigo',
            'reporte__unidad_organizacional__nombre',
        )
        .annotate(
            total_actividades=Count('id'),
            avance_fisico_promedio=Avg('porcentaje_avance_fisico'),
            avance_financiero_promedio=Avg('porcentaje_avance_financiero'),
        )
        .order_by('reporte__unidad_organizacional__codigo')
    )

    unidades = []
    for u in unidades_consolidado:
        avance_f = _safe_decimal(u['avance_fisico_promedio'])
        unidades.append({
            'codigo': u['reporte__unidad_organizacional__codigo'],
            'nombre': u['reporte__unidad_organizacional__nombre'],
            'total_actividades': u['total_actividades'],
            'avance_fisico_promedio': round(avance_f, 2),
            'avance_financiero_promedio': round(
                _safe_decimal(u['avance_financiero_promedio']), 2
            ),
            'semaforo': determinar_semaforo(avance_f),
        })

    return {
        'gestion': gestion,
        'total_actividades': total,
        'semaforo': {
            'verde': verde,
            'amarillo': amarillo,
            'rojo': rojo,
            'porcentaje_verde': round(_safe_divide(verde, total) * 100, 1),
            'porcentaje_amarillo': round(_safe_divide(amarillo, total) * 100, 1),
            'porcentaje_rojo': round(_safe_divide(rojo, total) * 100, 1),
        },
        'promedio_avance_fisico': round(promedio_fisico, 2),
        'promedio_avance_financiero': round(promedio_financiero, 2),
        'alertas_activas': alertas_activas,
        'alertas_por_tipo': list(alertas_por_tipo),
        'unidades': unidades,
    }


def _dashboard_vacio(gestion):
    """Retorna estructura vacia del dashboard."""
    return {
        'gestion': gestion,
        'total_actividades': 0,
        'semaforo': {
            'verde': 0, 'amarillo': 0, 'rojo': 0,
            'porcentaje_verde': 0, 'porcentaje_amarillo': 0, 'porcentaje_rojo': 0,
        },
        'promedio_avance_fisico': 0,
        'promedio_avance_financiero': 0,
        'alertas_activas': 0,
        'alertas_por_tipo': [],
        'unidades': [],
    }
