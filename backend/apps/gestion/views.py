from rest_framework import viewsets

from apps.accounts.permissions import TieneCapacidad

from .models import GestionFiscal, CicloFormulacion, EtapaFormulacion
from .serializers import (
    GestionFiscalSerializer,
    CicloFormulacionSerializer,
    EtapaFormulacionSerializer,
)

# Misma capacidad que gobierna habilitar/cerrar en V2 (`apps/budget/views.py`).
CAPACIDAD_GESTION = 'sis_poa.budget.manage'

ACCIONES_DE_ESCRITURA = ('create', 'update', 'partial_update', 'destroy')


class _EscrituraGobernadaMixin:
    """La lectura queda abierta; escribir exige la capacidad de gestión.

    El candado de SIS-POA no vale nada si la puerta de al lado deja editar la
    gestión sin permiso: hasta este cambio cualquier usuario autenticado podía
    `PATCH` sobre `/api/v1/gestiones/`.
    """

    def get_permissions(self):
        if self.action in ACCIONES_DE_ESCRITURA:
            return [TieneCapacidad(CAPACIDAD_GESTION)]
        return super().get_permissions()


class GestionFiscalViewSet(_EscrituraGobernadaMixin, viewsets.ModelViewSet):
    queryset = GestionFiscal.objects.all()
    serializer_class = GestionFiscalSerializer
    search_fields = ['anio', 'descripcion']
    ordering_fields = ['anio']


class CicloFormulacionViewSet(_EscrituraGobernadaMixin, viewsets.ModelViewSet):
    queryset = CicloFormulacion.objects.all()
    serializer_class = CicloFormulacionSerializer


class EtapaFormulacionViewSet(_EscrituraGobernadaMixin, viewsets.ModelViewSet):
    queryset = EtapaFormulacion.objects.all()
    serializer_class = EtapaFormulacionSerializer
