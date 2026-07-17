import django_filters
from .models import TechoPresupuestario, DistribucionTecho, MovimientoTecho


class TechoPresupuestarioFilter(django_filters.FilterSet):
    class Meta:
        model = TechoPresupuestario
        fields = {
            'gestion': ['exact'],
            'fuente': ['exact'],
            'organismo': ['exact'],
            'activo': ['exact'],
            'version': ['exact'],
            'monto_total': ['gte', 'lte'],
        }


class DistribucionTechoFilter(django_filters.FilterSet):
    class Meta:
        model = DistribucionTecho
        fields = {
            'techo': ['exact'],
            'da': ['exact'],
            'ue': ['exact'],
            'unidad': ['exact'],
            'programa': ['exact'],
            'activo': ['exact'],
            'version': ['exact'],
            'monto_asignado': ['gte', 'lte'],
        }


class MovimientoTechoFilter(django_filters.FilterSet):
    class Meta:
        model = MovimientoTecho
        fields = {
            'techo': ['exact'],
            'movement_type': ['exact'],
            'requested_by': ['exact'],
            'approved_by': ['exact'],
            'date': ['exact', 'gte', 'lte'],
        }
