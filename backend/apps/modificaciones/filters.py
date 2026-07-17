import django_filters
from .models import SolicitudModificacion, CambioModificacion, ImpactoModificacion


class SolicitudModificacionFilter(django_filters.FilterSet):
    class Meta:
        model = SolicitudModificacion
        fields = {
            'tipo': ['exact'],
            'gestion_fiscal': ['exact'],
            'entidad_afectada_tipo': ['exact'],
            'entidad_afectada_id': ['exact'],
            'poau': ['exact'],
            'solicitado_por': ['exact'],
            'estado': ['exact'],
            'fecha_efectiva': ['exact', 'gte', 'lte'],
            'version': ['exact'],
        }


class CambioModificacionFilter(django_filters.FilterSet):
    class Meta:
        model = CambioModificacion
        fields = {
            'solicitud': ['exact'],
            'campo': ['exact', 'icontains'],
        }


class ImpactoModificacionFilter(django_filters.FilterSet):
    class Meta:
        model = ImpactoModificacion
        fields = {
            'solicitud': ['exact'],
            'impacto_financiero': ['gte', 'lte'],
        }
