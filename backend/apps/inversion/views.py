from rest_framework import viewsets
from .models import ProyectoInversion, ProgramacionPlurianualProyecto, ProgramacionFisicaFinanciera
from .serializers import (
    ProyectoInversionSerializer, ProgramacionPlurianualProyectoSerializer,
    ProgramacionFisicaFinancieraSerializer
)


class ProyectoInversionViewSet(viewsets.ModelViewSet):
    queryset = ProyectoInversion.objects.all()
    serializer_class = ProyectoInversionSerializer
    filterset_fields = ['ue', 'programa', 'etapa', 'prioridad', 'activo']
    search_fields = ['codigo_interno', 'codigo_sisin', 'nombre']


class ProgramacionPlurianualProyectoViewSet(viewsets.ModelViewSet):
    queryset = ProgramacionPlurianualProyecto.objects.all()
    serializer_class = ProgramacionPlurianualProyectoSerializer
    filterset_fields = ['proyecto', 'anio']


class ProgramacionFisicaFinancieraViewSet(viewsets.ModelViewSet):
    queryset = ProgramacionFisicaFinanciera.objects.all()
    serializer_class = ProgramacionFisicaFinancieraSerializer
    filterset_fields = ['proyecto', 'gestion']
