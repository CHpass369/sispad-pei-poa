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
    def presupuesto(self, request):
        """GET /api/v1/dashboard/presupuesto/?gestion=2026"""
        gestion = request.query_params.get('gestion', 2026)
        try:
            data = dashboard_presupuesto(int(gestion))
            return Response(data)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
