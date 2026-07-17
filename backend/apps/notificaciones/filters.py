import django_filters
from .models import TipoNotificacion, Notificacion, PreferenciaNotificacion


class TipoNotificacionFilter(django_filters.FilterSet):
    class Meta:
        model = TipoNotificacion
        fields = {
            'codigo': ['exact'],
            'nombre': ['icontains'],
            'is_active': ['exact'],
        }


class NotificacionFilter(django_filters.FilterSet):
    class Meta:
        model = Notificacion
        fields = {
            'user': ['exact'],
            'tipo': ['exact'],
            'titulo': ['icontains'],
            'is_read': ['exact'],
            'priority': ['exact'],
            'entity_type': ['exact'],
            'entity_id': ['exact'],
            'gestion': ['exact'],
            'created_at': ['exact', 'gte', 'lte'],
        }


class PreferenciaNotificacionFilter(django_filters.FilterSet):
    class Meta:
        model = PreferenciaNotificacion
        fields = {
            'user': ['exact'],
            'receive_internal': ['exact'],
            'receive_email': ['exact'],
            'frequency': ['exact'],
        }
