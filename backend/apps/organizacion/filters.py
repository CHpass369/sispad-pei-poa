import django_filters
from .models import TipoUnidad, UnidadOrganizacional, DireccionAdministrativa, UnidadEjecutora, AsignacionUsuarioUnidad


class TipoUnidadFilter(django_filters.FilterSet):
    class Meta:
        model = TipoUnidad
        fields = {
            'codigo': ['exact'],
            'nombre': ['exact', 'icontains'],
            'nivel': ['exact', 'lte', 'gte'],
            'activo': ['exact'],
        }


class UnidadOrganizacionalFilter(django_filters.FilterSet):
    class Meta:
        model = UnidadOrganizacional
        fields = {
            'codigo': ['exact', 'icontains'],
            'nombre': ['icontains'],
            'tipo': ['exact'],
            'padre': ['exact'],
            'responsable': ['exact'],
            'gestion': ['exact'],
            'activo': ['exact'],
        }


class DireccionAdministrativaFilter(django_filters.FilterSet):
    class Meta:
        model = DireccionAdministrativa
        fields = {
            'codigo': ['exact'],
            'nombre': ['icontains'],
            'gestion': ['exact'],
            'responsable': ['exact'],
            'activo': ['exact'],
        }


class UnidadEjecutoraFilter(django_filters.FilterSet):
    class Meta:
        model = UnidadEjecutora
        fields = {
            'codigo': ['exact'],
            'nombre': ['icontains'],
            'da': ['exact'],
            'gestion': ['exact'],
            'responsable': ['exact'],
            'activo': ['exact'],
        }


class AsignacionUsuarioUnidadFilter(django_filters.FilterSet):
    class Meta:
        model = AsignacionUsuarioUnidad
        fields = {
            'usuario': ['exact'],
            'unidad': ['exact'],
            'gestion': ['exact'],
            'es_responsable_poa': ['exact'],
            'activo': ['exact'],
        }
