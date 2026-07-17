import django_filters
from .models import Distrito, UnidadTerritorial, LocalizacionTerritorial


class DistritoFilter(django_filters.FilterSet):
    class Meta:
        model = Distrito
        fields = {
            'codigo': ['exact', 'icontains'],
            'nombre': ['icontains'],
        }


class UnidadTerritorialFilter(django_filters.FilterSet):
    class Meta:
        model = UnidadTerritorial
        fields = {
            'codigo': ['exact', 'icontains'],
            'nombre': ['icontains'],
            'tipo': ['exact'],
            'distrito': ['exact'],
        }


class LocalizacionTerritorialFilter(django_filters.FilterSet):
    class Meta:
        model = LocalizacionTerritorial
        fields = {
            'entidad': ['exact'],
            'entidad_id': ['exact'],
            'distrito': ['exact'],
            'unidad_territorial': ['exact'],
            'gestion': ['exact'],
            'activo': ['exact'],
        }
