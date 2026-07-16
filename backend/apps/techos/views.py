from rest_framework import viewsets
from .models import TechoPresupuestario, DistribucionTecho
from .serializers import TechoPresupuestarioSerializer, DistribucionTechoSerializer


class TechoPresupuestarioViewSet(viewsets.ModelViewSet):
    queryset = TechoPresupuestario.objects.all()
    serializer_class = TechoPresupuestarioSerializer
    filterset_fields = ['gestion', 'fuente', 'activo']


class DistribucionTechoViewSet(viewsets.ModelViewSet):
    queryset = DistribucionTecho.objects.all()
    serializer_class = DistribucionTechoSerializer
    filterset_fields = ['techo', 'da', 'ue', 'unidad', 'programa', 'activo']
