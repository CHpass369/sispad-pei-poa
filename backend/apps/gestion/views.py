from rest_framework import viewsets
from .models import GestionFiscal, CicloFormulacion, EtapaFormulacion
from .serializers import GestionFiscalSerializer, CicloFormulacionSerializer, EtapaFormulacionSerializer


class GestionFiscalViewSet(viewsets.ModelViewSet):
    queryset = GestionFiscal.objects.all()
    serializer_class = GestionFiscalSerializer
    search_fields = ['anio', 'descripcion']
    ordering_fields = ['anio']


class CicloFormulacionViewSet(viewsets.ModelViewSet):
    queryset = CicloFormulacion.objects.all()
    serializer_class = CicloFormulacionSerializer


class EtapaFormulacionViewSet(viewsets.ModelViewSet):
    queryset = EtapaFormulacion.objects.all()
    serializer_class = EtapaFormulacionSerializer
