import django_filters
from .models import VersionNormativa, ReglaPresupuestariaLegal


class VersionNormativaFilter(django_filters.FilterSet):
    class Meta:
        model = VersionNormativa
        fields = {
            'titulo': ['icontains'],
            'tipo': ['exact'],
            'numero': ['exact', 'icontains'],
            'gestion': ['exact'],
            'activo': ['exact'],
        }


class ReglaPresupuestariaLegalFilter(django_filters.FilterSet):
    class Meta:
        model = ReglaPresupuestariaLegal
        fields = {
            'codigo': ['exact'],
            'nombre': ['icontains'],
            'tipo': ['exact'],
            'severidad': ['exact'],
            'gestion_desde': ['exact', 'lte', 'gte'],
            'gestion_hasta': ['exact', 'lte', 'gte'],
            'activo': ['exact'],
        }
