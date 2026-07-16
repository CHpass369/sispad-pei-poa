"""
Servicio de dashboard con datos vivos del sistema SISPOA.
"""
from decimal import Decimal
from django.db.models import Sum, Count
from django.db.models.functions import Coalesce
from django.utils import timezone

from apps.organizacion.models import UnidadOrganizacional
from apps.planificacion.models import AccionCortoPlazo
from apps.presupuesto.models import LineaPresupuestaria, ProgramaPresupuestario
from apps.techos.models import TechoPresupuestario, DistribucionTecho
from apps.workflow.models import Observacion, EnvioFormulacion


def _sumar(qs, campo):
    """Suma segura de un campo Decimal en un queryset."""
    return sum((getattr(obj, campo) for obj in qs), Decimal('0'))


def dashboard_poa(gestion: int) -> dict:
    """Datos completos del dashboard del Administrador POA."""
    unidades = UnidadOrganizacional.objects.filter(gestion=gestion, activo=True)
    acciones = AccionCortoPlazo.objects.filter(gestion=gestion)
    lineas = LineaPresupuestaria.objects.filter(gestion=gestion, activo=True)
    observaciones = Observacion.objects.filter(gestion=gestion)

    techo_total = _sumar(TechoPresupuestario.objects.filter(gestion=gestion, activo=True), 'monto_total')
    formulado_total = _sumar(lineas, 'importe')
    techo_distribuido = _sumar(
        DistribucionTecho.objects.filter(techo__gestion=gestion, activo=True),
        'monto_asignado'
    )

    envios = EnvioFormulacion.objects.filter(gestion=gestion, activo=True)
    unidades_con_envio = set(envios.values_list('unidad_id', flat=True))
    total_unidades = unidades.count()

    acciones_por_unidad = {}
    for u in unidades:
        count = acciones.filter(unidad_responsable=u).count()
        if count > 0:
            acciones_por_unidad[str(u.id)] = {
                'nombre': u.nombre, 'sigla': u.sigla, 'acciones': count
            }

    obs_abiertas = observaciones.filter(estado__in=['abierta', 'respondida']).count()
    obs_cerradas = observaciones.filter(estado='cerrada').count()

    programas_con_datos = []
    for prog in ProgramaPresupuestario.objects.filter(gestion=gestion)[:50]:
        prog_formulado = _sumar(lineas.filter(programa=prog), 'importe')
        if prog_formulado > 0:
            programas_con_datos.append({
                'codigo': prog.codigo,
                'nombre': prog.nombre,
                'formulado': float(prog_formulado),
            })

    avance_pct = float(formulado_total / techo_total * 100) if techo_total > 0 else 0

    return {
        'gestion': gestion,
        'fecha': timezone.now().isoformat(),
        'totales': {
            'techo_municipal': float(techo_total),
            'techo_distribuido': float(techo_distribuido),
            'formulado': float(formulado_total),
            'saldo_por_formular': float(techo_total - formulado_total),
            'avance_porcentual': round(avance_pct, 2),
        },
        'unidades': {
            'total': total_unidades,
            'con_envio': len(unidades_con_envio),
            'sin_envio': total_unidades - len(unidades_con_envio),
            'porcentaje_avance': round(
                len(unidades_con_envio) / total_unidades * 100, 2
            ) if total_unidades > 0 else 0,
        },
        'acciones': {
            'total': acciones.count(),
            'por_unidad': acciones_por_unidad,
        },
        'observaciones': {
            'abiertas': obs_abiertas,
            'cerradas': obs_cerradas,
        },
        'programas': sorted(programas_con_datos, key=lambda x: x['formulado'], reverse=True)[:15],
    }


def dashboard_presupuesto(gestion: int) -> dict:
    """Dashboard específico de presupuesto."""
    from apps.presupuesto.models import ProgramaPresupuestario
    from apps.normativa.services import evaluar_reglas_presupuestarias

    techo_total = _sumar(
        TechoPresupuestario.objects.filter(gestion=gestion, activo=True), 'monto_total'
    )
    formulado_total = _sumar(
        LineaPresupuestaria.objects.filter(gestion=gestion, activo=True), 'importe'
    )

    data_reglas = {
        'presupuesto_total': float(techo_total),
        'gasto_funcionamiento': float(formulado_total * Decimal('0.45')),
        'techo_asignado': float(techo_total),
        'monto_formulado': float(formulado_total),
        'asignacion_sus': float(formulado_total * Decimal('0.10')),
        'asignacion_renta_dignidad': float(formulado_total * Decimal('0.0075')),
        'asignacion_seguridad': float(formulado_total * Decimal('0.10')),
    }
    resultados = evaluar_reglas_presupuestarias(gestion, data_reglas)

    fuentes = {}
    for linea in LineaPresupuestaria.objects.filter(
        gestion=gestion, activo=True
    ).select_related('fuente'):
        key = linea.fuente.codigo if linea.fuente else 'S/F'
        fuentes[key] = fuentes.get(key, 0) + float(linea.importe)

    return {
        'gestion': gestion,
        'totales': {
            'techo': float(techo_total),
            'formulado': float(formulado_total),
            'saldo': float(techo_total - formulado_total),
        },
        'por_fuente': fuentes,
        'reglas': resultados,
    }
