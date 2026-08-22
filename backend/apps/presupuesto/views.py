from rest_framework import viewsets

from apps.gestion.mixins import CandadoSisPoaMixin

from .models import ProgramaPresupuestario, ProyectoPresupuestario, ActividadPresupuestaria, LineaPresupuestaria
from .serializers import (
    ProgramaPresupuestarioSerializer, ProyectoPresupuestarioSerializer,
    ActividadPresupuestariaSerializer, LineaPresupuestariaSerializer
)

# La estructura programática es de la gestión habilitada: `gestion` sale de los
# filtros libres y la pone el candado de SIS-POA (ADR-007).


class ProgramaPresupuestarioViewSet(CandadoSisPoaMixin, viewsets.ModelViewSet):
    queryset = ProgramaPresupuestario.objects.all()
    serializer_class = ProgramaPresupuestarioSerializer
    filterset_fields = ['ue_responsable', 'activo']
    search_fields = ['codigo', 'nombre']


class ProyectoPresupuestarioViewSet(CandadoSisPoaMixin, viewsets.ModelViewSet):
    queryset = ProyectoPresupuestario.objects.all()
    serializer_class = ProyectoPresupuestarioSerializer
    filterset_fields = ['programa', 'activo']


class ActividadPresupuestariaViewSet(CandadoSisPoaMixin, viewsets.ModelViewSet):
    queryset = ActividadPresupuestaria.objects.all()
    serializer_class = ActividadPresupuestariaSerializer
    filterset_fields = ['proyecto', 'activo']


class LineaPresupuestariaViewSet(CandadoSisPoaMixin, viewsets.ModelViewSet):
    queryset = LineaPresupuestaria.objects.all()
    serializer_class = LineaPresupuestariaSerializer
    filterset_fields = ['programa', 'ue', 'fuente', 'objeto_gasto', 'activo']
