from rest_framework import viewsets
from .models import Distrito, UnidadTerritorial, LocalizacionTerritorial
from .serializers import DistritoSerializer, UnidadTerritorialSerializer, LocalizacionTerritorialSerializer


class DistritoViewSet(viewsets.ModelViewSet):
    queryset = Distrito.objects.all()
    serializer_class = DistritoSerializer
    search_fields = ['codigo', 'nombre']


class UnidadTerritorialViewSet(viewsets.ModelViewSet):
    queryset = UnidadTerritorial.objects.all()
    serializer_class = UnidadTerritorialSerializer
    filterset_fields = ['distrito', 'tipo']
    search_fields = ['codigo', 'nombre']


class LocalizacionTerritorialViewSet(viewsets.ModelViewSet):
    queryset = LocalizacionTerritorial.objects.all()
    serializer_class = LocalizacionTerritorialSerializer
    filterset_fields = ['gestion', 'distrito', 'activo']
