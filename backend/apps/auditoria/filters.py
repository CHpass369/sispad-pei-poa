import django_filters
from .models import EventoAuditoria


class EventoAuditoriaFilter(django_filters.FilterSet):
    class Meta:
        model = EventoAuditoria
        fields = {
            'usuario': ['exact'],
            'accion': ['exact'],
            'entidad': ['exact'],
            'entidad_id': ['exact'],
            'gestion': ['exact'],
            'creado_en': ['exact', 'gte', 'lte'],
        }
