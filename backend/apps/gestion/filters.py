import django_filters
from .models import GestionFiscal, CicloFormulacion, EtapaFormulacion


class GestionFiscalFilter(django_filters.FilterSet):
    class Meta:
        model = GestionFiscal
        fields = {
            'anio': ['exact', 'gte', 'lte'],
            'estado': ['exact'],
            'activa': ['exact'],
        }


class CicloFormulacionFilter(django_filters.FilterSet):
    class Meta:
        model = CicloFormulacion
        fields = {
            'gestion': ['exact'],
            'nombre': ['icontains'],
            'activo': ['exact'],
        }


class EtapaFormulacionFilter(django_filters.FilterSet):
    class Meta:
        model = EtapaFormulacion
        fields = {
            'ciclo': ['exact'],
            'codigo': ['exact'],
            'completada': ['exact'],
        }
