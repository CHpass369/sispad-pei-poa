import django_filters
from .models import DocumentoAdjunto


class DocumentoAdjuntoFilter(django_filters.FilterSet):
    class Meta:
        model = DocumentoAdjunto
        fields = {
            'entidad': ['exact'],
            'entidad_id': ['exact'],
            'nombre': ['icontains'],
            'tipo_documento': ['exact', 'icontains'],
            'gestion': ['exact'],
            'subido_por': ['exact'],
            'activo': ['exact'],
        }
