import django_filters
from .models import EnvioFormulacion, Revision, Observacion, Aprobacion


class EnvioFormulacionFilter(django_filters.FilterSet):
    class Meta:
        model = EnvioFormulacion
        fields = {
            'unidad': ['exact'],
            'gestion': ['exact'],
            'version': ['exact'],
            'enviado_por': ['exact'],
            'activo': ['exact'],
        }


class RevisionFilter(django_filters.FilterSet):
    class Meta:
        model = Revision
        fields = {
            'envio': ['exact'],
            'tipo_revision': ['exact'],
            'revisor': ['exact'],
            'estado': ['exact'],
            'resultado': ['exact'],
        }


class ObservacionFilter(django_filters.FilterSet):
    class Meta:
        model = Observacion
        fields = {
            'revision': ['exact'],
            'tipo': ['exact'],
            'severidad': ['exact'],
            'modulo': ['exact'],
            'responsable_subsanacion': ['exact'],
            'estado': ['exact'],
            'gestion': ['exact'],
        }


class AprobacionFilter(django_filters.FilterSet):
    class Meta:
        model = Aprobacion
        fields = {
            'gestion': ['exact'],
            'tipo': ['exact'],
            'aprobado_por': ['exact'],
            'estado': ['exact'],
            'version': ['exact'],
            'es_reapertura': ['exact'],
        }
