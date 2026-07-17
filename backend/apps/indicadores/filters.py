import django_filters
from .models import Indicador, MetaProgramada, Operacion, Tarea, Producto, MedioVerificacion, Supuesto


class IndicadorFilter(django_filters.FilterSet):
    class Meta:
        model = Indicador
        fields = {
            'codigo': ['exact', 'icontains'],
            'nombre': ['icontains'],
            'tipo_comportamiento': ['exact'],
            'unidad_medida': ['exact'],
            'responsable': ['exact'],
            'activo': ['exact'],
        }


class MetaProgramadaFilter(django_filters.FilterSet):
    class Meta:
        model = MetaProgramada
        fields = {
            'indicador': ['exact'],
            'gestion': ['exact'],
            'version': ['exact'],
        }


class OperacionFilter(django_filters.FilterSet):
    class Meta:
        model = Operacion
        fields = {
            'accion_corto_plazo': ['exact'],
            'codigo': ['exact', 'icontains'],
            'nombre': ['icontains'],
            'tipo': ['exact'],
            'activo': ['exact'],
        }


class TareaFilter(django_filters.FilterSet):
    class Meta:
        model = Tarea
        fields = {
            'operacion': ['exact'],
            'codigo': ['exact', 'icontains'],
            'nombre': ['icontains'],
            'activo': ['exact'],
        }


class ProductoFilter(django_filters.FilterSet):
    class Meta:
        model = Producto
        fields = {
            'accion_corto_plazo': ['exact'],
            'codigo': ['exact', 'icontains'],
            'tipo': ['exact'],
            'estado': ['exact'],
            'tipo_producto': ['exact'],
            'activo': ['exact'],
        }


class MedioVerificacionFilter(django_filters.FilterSet):
    class Meta:
        model = MedioVerificacion
        fields = {
            'indicador': ['exact'],
            'nombre': ['icontains'],
        }


class SupuestoFilter(django_filters.FilterSet):
    class Meta:
        model = Supuesto
        fields = {
            'accion_corto_plazo': ['exact'],
        }
