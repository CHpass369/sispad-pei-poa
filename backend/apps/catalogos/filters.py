import django_filters
from .models import (
    ClasificadorInstitucional, RubroRecurso, ObjetoGasto, FuenteFinanciamiento,
    OrganismoFinanciador, EntidadTransferencia, FinalidadFuncion, UnidadMedida,
    TipoOperacion, TipoProducto, TipoProyecto, TipoFinanciamiento, VersionCatalogo,
)


class ClasificadorInstitucionalFilter(django_filters.FilterSet):
    class Meta:
        model = ClasificadorInstitucional
        fields = {
            'codigo': ['exact', 'icontains'],
            'denominacion': ['exact', 'icontains'],
            'gestion': ['exact'],
            'activo': ['exact'],
        }


class RubroRecursoFilter(django_filters.FilterSet):
    class Meta:
        model = RubroRecurso
        fields = {
            'codigo': ['exact', 'icontains'],
            'denominacion': ['exact', 'icontains'],
            'gestion': ['exact'],
            'activo': ['exact'],
        }


class ObjetoGastoFilter(django_filters.FilterSet):
    class Meta:
        model = ObjetoGasto
        fields = {
            'codigo': ['exact', 'icontains'],
            'denominacion': ['exact', 'icontains'],
            'gestion': ['exact'],
            'activo': ['exact'],
        }


class FuenteFinanciamientoFilter(django_filters.FilterSet):
    class Meta:
        model = FuenteFinanciamiento
        fields = {
            'codigo': ['exact', 'icontains'],
            'denominacion': ['exact', 'icontains'],
            'gestion': ['exact'],
            'activo': ['exact'],
        }


class OrganismoFinanciadorFilter(django_filters.FilterSet):
    class Meta:
        model = OrganismoFinanciador
        fields = {
            'codigo': ['exact', 'icontains'],
            'denominacion': ['exact', 'icontains'],
            'gestion': ['exact'],
            'activo': ['exact'],
        }


class EntidadTransferenciaFilter(django_filters.FilterSet):
    class Meta:
        model = EntidadTransferencia
        fields = {
            'codigo': ['exact', 'icontains'],
            'denominacion': ['exact', 'icontains'],
            'gestion': ['exact'],
            'activo': ['exact'],
        }


class FinalidadFuncionFilter(django_filters.FilterSet):
    class Meta:
        model = FinalidadFuncion
        fields = {
            'codigo': ['exact', 'icontains'],
            'denominacion': ['exact', 'icontains'],
            'gestion': ['exact'],
            'activo': ['exact'],
        }


class UnidadMedidaFilter(django_filters.FilterSet):
    class Meta:
        model = UnidadMedida
        fields = {
            'codigo': ['exact', 'icontains'],
            'denominacion': ['exact', 'icontains'],
            'gestion': ['exact'],
            'activo': ['exact'],
        }


class TipoOperacionFilter(django_filters.FilterSet):
    class Meta:
        model = TipoOperacion
        fields = {
            'codigo': ['exact', 'icontains'],
            'denominacion': ['exact', 'icontains'],
            'gestion': ['exact'],
            'activo': ['exact'],
        }


class TipoProductoFilter(django_filters.FilterSet):
    class Meta:
        model = TipoProducto
        fields = {
            'codigo': ['exact', 'icontains'],
            'denominacion': ['exact', 'icontains'],
            'gestion': ['exact'],
            'activo': ['exact'],
        }


class TipoProyectoFilter(django_filters.FilterSet):
    class Meta:
        model = TipoProyecto
        fields = {
            'codigo': ['exact', 'icontains'],
            'denominacion': ['exact', 'icontains'],
            'gestion': ['exact'],
            'activo': ['exact'],
        }


class TipoFinanciamientoFilter(django_filters.FilterSet):
    class Meta:
        model = TipoFinanciamiento
        fields = {
            'codigo': ['exact', 'icontains'],
            'denominacion': ['exact', 'icontains'],
            'gestion': ['exact'],
            'activo': ['exact'],
        }


class VersionCatalogoFilter(django_filters.FilterSet):
    class Meta:
        model = VersionCatalogo
        fields = {
            'nombre': ['icontains'],
            'gestion': ['exact'],
            'aplicado': ['exact'],
        }
