"""
Servicio de dashboard con datos vivos del sistema SISPOA.
"""
from decimal import Decimal
from django.db.models import Sum, Count, Value, DecimalField
from django.db.models.functions import Coalesce
from django.utils import timezone

from apps.organizacion.models import UnidadOrganizacional
from apps.planificacion.models import AccionCortoPlazo
from apps.presupuesto.models import LineaPresupuestaria, ProgramaPresupuestario
from apps.techos.models import TechoPresupuestario, DistribucionTecho
from apps.workflow.models import Observacion, EnvioFormulacion


def dashboard_poa(gestion: int) -> dict:
    """Datos completos del dashboard del Administrador POA — optimizado sin N+1."""
    D = DecimalField()
    V = Value(0, output_field=D)
    
    # Agregaciones con SQL (sin loops Python)
    techo_agg = TechoPresupuestario.objects.filter(
        gestion=gestion, activo=True
    ).aggregate(total=Coalesce(Sum('monto_total', output_field=D), V, output_field=D))

    formulado_agg = LineaPresupuestaria.objects.filter(
        gestion=gestion, activo=True
    ).aggregate(total=Coalesce(Sum('importe', output_field=D), V, output_field=D))

    techo_dist_agg = DistribucionTecho.objects.filter(
        techo__gestion=gestion, activo=True
    ).aggregate(total=Coalesce(Sum('monto_asignado', output_field=D), V, output_field=D))

    techo_total = float(techo_agg['total'])
    formulado_total = float(formulado_agg['total'])
    techo_distribuido = float(techo_dist_agg['total'])
    avance_pct = round(formulado_total / techo_total * 100, 2) if techo_total > 0 else 0

    # Conteos SQL
    total_unidades = UnidadOrganizacional.objects.filter(gestion=gestion, activo=True).count()
    unidades_con_envio = EnvioFormulacion.objects.filter(
        gestion=gestion, activo=True
    ).values('unidad_id').distinct().count()

    total_acciones = AccionCortoPlazo.objects.filter(gestion=gestion).count()

    obs_abiertas = Observacion.objects.filter(
        gestion=gestion, estado__in=['abierta', 'respondida']
    ).count()
    obs_cerradas = Observacion.objects.filter(gestion=gestion, estado='cerrada').count()

    # Top 5 unidades con más acciones (con SQL)
    from django.db.models import Count
    top_unidades = AccionCortoPlazo.objects.filter(gestion=gestion)\
        .values('unidad_responsable__nombre', 'unidad_responsable__sigla')\
        .annotate(total=Count('id'))\
        .order_by('-total')[:5]

    # Top 10 programas por presupuesto formulado (con SQL)
    top_programas = LineaPresupuestaria.objects.filter(
        gestion=gestion, activo=True
    ).values('programa__codigo', 'programa__nombre')\
        .annotate(total=Coalesce(Sum('importe', output_field=D), V, output_field=D))\
        .filter(total__gt=0)\
        .order_by('-total')[:10]

    return {
        'gestion': gestion,
        'fecha': timezone.now().isoformat(),
        'presupuesto_total': techo_total,
        'formulado': formulado_total,
        'saldo': techo_total - formulado_total,
        'avance': avance_pct,
        'aprobaciones_pendientes': obs_abiertas,
        'alertas_count': 0,
        'unidades': {
            'total': total_unidades,
            'con_envio': unidades_con_envio,
        },
        'acciones': {
            'total': total_acciones,
        },
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
