import django_filters
from .models import POAU, POAUActividad, EjecucionFisica, EjecucionFinanciera


class POAUFilter(django_filters.FilterSet):
    class Meta:
        model = POAU
        fields = {
            'unidad': ['exact'],
            'producto_territorial': ['exact'],
            'gestion': ['exact'],
            'codigo': ['exact', 'icontains'],
            'nombre': ['icontains'],
            'estado': ['exact'],
            'responsable': ['exact'],
        }


class POAUActividadFilter(django_filters.FilterSet):
    class Meta:
        model = POAUActividad
        fields = {
            'poau': ['exact'],
            'codigo': ['exact', 'icontains'],
            'nombre': ['icontains'],
            'objeto_gasto': ['exact'],
            'accion_corto_plazo': ['exact'],
        }


class EjecucionFisicaFilter(django_filters.FilterSet):
    class Meta:
        model = EjecucionFisica
        fields = {
            'actividad': ['exact'],
            'periodo': ['exact', 'icontains'],
            'tipo_periodo': ['exact'],
        }


class EjecucionFinancieraFilter(django_filters.FilterSet):
    class Meta:
        model = EjecucionFinanciera
        fields = {
            'actividad': ['exact'],
            'periodo': ['exact', 'icontains'],
            'tipo_periodo': ['exact'],
        }
