from rest_framework import viewsets
from .models import EstimacionRecurso, EstimacionPlurianual
from .serializers import EstimacionRecursoSerializer, EstimacionPlurianualSerializer


class EstimacionRecursoViewSet(viewsets.ModelViewSet):
    queryset = EstimacionRecurso.objects.all()
    serializer_class = EstimacionRecursoSerializer
    filterset_fields = ['gestion', 'rubro', 'fuente', 'activo']


class EstimacionPlurianualViewSet(viewsets.ModelViewSet):
    queryset = EstimacionPlurianual.objects.all()
    serializer_class = EstimacionPlurianualSerializer
    filterset_fields = ['estimacion_origen', 'anio']
