from rest_framework import viewsets
from .models import ProgramaPresupuestario, ProyectoPresupuestario, ActividadPresupuestaria, LineaPresupuestaria
from .serializers import (
    ProgramaPresupuestarioSerializer, ProyectoPresupuestarioSerializer,
    ActividadPresupuestariaSerializer, LineaPresupuestariaSerializer
)


class ProgramaPresupuestarioViewSet(viewsets.ModelViewSet):
    queryset = ProgramaPresupuestario.objects.all()
    serializer_class = ProgramaPresupuestarioSerializer
    filterset_fields = ['gestion', 'ue_responsable', 'activo']
    search_fields = ['codigo', 'nombre']


class ProyectoPresupuestarioViewSet(viewsets.ModelViewSet):
    queryset = ProyectoPresupuestario.objects.all()
    serializer_class = ProyectoPresupuestarioSerializer
    filterset_fields = ['programa', 'gestion', 'activo']


class ActividadPresupuestariaViewSet(viewsets.ModelViewSet):
    queryset = ActividadPresupuestaria.objects.all()
    serializer_class = ActividadPresupuestariaSerializer
    filterset_fields = ['proyecto', 'gestion', 'activo']


class LineaPresupuestariaViewSet(viewsets.ModelViewSet):
    queryset = LineaPresupuestaria.objects.all()
    serializer_class = LineaPresupuestariaSerializer
    filterset_fields = ['gestion', 'programa', 'ue', 'fuente', 'objeto_gasto', 'activo']
