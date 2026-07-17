import django_filters
from .models import ReporteGenerado


class ReporteGeneradoFilter(django_filters.FilterSet):
    class Meta:
        model = ReporteGenerado
        fields = {
            'nombre': ['icontains'],
            'tipo': ['exact'],
            'formato': ['exact'],
            'gestion': ['exact'],
            'generado_por': ['exact'],
        }
