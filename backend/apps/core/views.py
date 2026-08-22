from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.gestion.mixins import gestion_del_candado

from .dashboard import dashboard_poa, dashboard_presupuesto


class DashboardViewSet(viewsets.ViewSet):
    """Dashboard con datos vivos del sistema.

    La gestión sale del candado de SIS-POA (ADR-007), no de un literal: los
    tres endpoints tenían `2026` clavado como default, así que sin `?gestion=`
    el tablero mostraba una gestión cerrada como si fuera la vigente.
    """

    @action(detail=False, methods=['get'])
    def poa(self, request):
        """GET /api/v1/dashboard/poa/"""
        return self._tablero(request, dashboard_poa)

    @action(detail=False, methods=['get'])
    def kpis(self, request):
        """GET /api/v1/dashboard/kpis/ — KPIs generales del dashboard."""
        return self._tablero(request, dashboard_poa)

    @action(detail=False, methods=['get'])
    def presupuesto(self, request):
        """GET /api/v1/dashboard/presupuesto/"""
        return self._tablero(request, dashboard_presupuesto)

    def _tablero(self, request, armar):
        gestion = gestion_del_candado(request)
        try:
            return Response(armar(gestion.anio))
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
