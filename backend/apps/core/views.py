from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .dashboard import dashboard_poa, dashboard_presupuesto


class DashboardViewSet(viewsets.ViewSet):
    """Dashboard con datos vivos del sistema."""

    @action(detail=False, methods=['get'])
    def poa(self, request):
        """GET /api/v1/dashboard/poa/?gestion=2026"""
        gestion = request.query_params.get('gestion', 2026)
        try:
            data = dashboard_poa(int(gestion))
            return Response(data)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def kpis(self, request):
        """GET /api/v1/dashboard/kpis/?gestion=2026
        KPIs generales para el dashboard principal.
        """
        gestion = request.query_params.get('gestion', 2026)
        try:
            from apps.presupuesto.models import LineaPresupuestaria
            from apps.workflow.models import Aprobacion
            from django.db.models import Sum

            lp = LineaPresupuestaria.objects.filter(gestion=int(gestion))
            total = float(lp.aggregate(t=Sum('importe'))['t'] or 0)
            aprob_pend = Aprobacion.objects.filter(gestion=int(gestion), estado__in=['pendiente']).count()

            data = {
                'presupuesto_total': total,
                'ejecucion_porcentaje': 0,
                'aprobaciones_pendientes': aprob_pend,
                'alertas_count': 0,
                'por_tipo': [],
                'por_mes': [],
                'actividad_reciente': [],
                'pei_avance': 0,
                'pad_avance': 0,
                'indicadores_ok': 0,
                'indicadores_total': 0,
                'evaluaciones_pendientes': 0,
            }
            return Response(data)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def presupuesto(self, request):
        """GET /api/v1/dashboard/presupuesto/?gestion=2026"""
        gestion = request.query_params.get('gestion', 2026)
        try:
            data = dashboard_presupuesto(int(gestion))
            return Response(data)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
