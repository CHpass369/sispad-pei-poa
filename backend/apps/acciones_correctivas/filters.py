import django_filters
from .models import AccionCorrectiva, CompromisoAccionCorrectiva


class AccionCorrectivaFilter(django_filters.FilterSet):
    class Meta:
        model = AccionCorrectiva
        fields = {
            'alerta': ['exact'],
            'entry': ['exact'],
            'responsible': ['exact'],
            'responsible_unit': ['exact'],
            'verified_by': ['exact'],
            'status': ['exact'],
            'gestion': ['exact'],
            'start_date': ['exact', 'gte', 'lte'],
            'due_date': ['exact', 'gte', 'lte'],
            'verified_at': ['exact', 'gte', 'lte'],
        }


class CompromisoAccionCorrectivaFilter(django_filters.FilterSet):
    class Meta:
        model = CompromisoAccionCorrectiva
        fields = {
            'accion_correctiva': ['exact'],
            'status': ['exact'],
            'due_date': ['exact', 'gte', 'lte'],
            'completed_at': ['exact', 'gte', 'lte'],
        }
