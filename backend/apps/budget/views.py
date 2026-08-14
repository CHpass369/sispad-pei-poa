"""API V2 del ciclo presupuestario SIS-POA (Fase 1: gestión fiscal).

Contrato:
    GET/POST   /api/v2/sis-poa/budget/fiscal-years/
    GET/PATCH  /api/v2/sis-poa/budget/fiscal-years/{id}/
    POST       /api/v2/sis-poa/budget/fiscal-years/{id}/enable/   → HABILITADA
    POST       /api/v2/sis-poa/budget/fiscal-years/{id}/close/    → CERRADA

Habilitar/cerrar exigen superusuario o capacidad `sis_poa.budget.manage`
(ADR-003); el resto de operaciones usan IsAuthenticated (default global).
"""
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.accounts.permissions import TieneCapacidad
from apps.gestion.models import GestionFiscal

from .serializers import FiscalYearSerializer
from .services import cerrar_gestion, habilitar_gestion

CAPACIDAD_GESTION = 'sis_poa.budget.manage'


class FiscalYearViewSet(viewsets.ModelViewSet):
    queryset = GestionFiscal.objects.all()
    serializer_class = FiscalYearSerializer
    filterset_fields = ['anio', 'estado', 'activa']
    search_fields = ['anio', 'descripcion']

    def get_permissions(self):
        if self.action in ('enable', 'close'):
            return [TieneCapacidad(CAPACIDAD_GESTION)]
        return super().get_permissions()

    def _ejecutar_servicio(self, request, pk, servicio):
        gestion = self.get_object()
        try:
            servicio(gestion, request.user)
        except DjangoValidationError as exc:
            return Response(
                {'error': {'detail': exc.messages}},
                status=400,
            )
        return Response(self.get_serializer(gestion).data)

    @action(detail=True, methods=['post'], url_path='enable')
    def enable(self, request, pk=None):
        """Habilita la gestión para el ciclo presupuestario (HABILITADA)."""
        return self._ejecutar_servicio(request, pk, habilitar_gestion)

    @action(detail=True, methods=['post'], url_path='close')
    def close(self, request, pk=None):
        """Cierra la gestión del ciclo presupuestario (CERRADA)."""
        return self._ejecutar_servicio(request, pk, cerrar_gestion)
