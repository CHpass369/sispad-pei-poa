import django_filters
from .models import EstimacionRecurso, EstimacionPlurianual


class EstimacionRecursoFilter(django_filters.FilterSet):
    class Meta:
        model = EstimacionRecurso
        fields = {
            'gestion': ['exact'],
            'rubro': ['exact'],
            'fuente': ['exact'],
            'organismo': ['exact'],
            'activo': ['exact'],
            'version': ['exact'],
            'monto_estimado': ['gte', 'lte'],
        }


class EstimacionPlurianualFilter(django_filters.FilterSet):
    class Meta:
        model = EstimacionPlurianual
        fields = {
            'estimacion_origen': ['exact'],
            'anio': ['exact', 'gte', 'lte'],
            'monto_proyectado': ['gte', 'lte'],
        }
