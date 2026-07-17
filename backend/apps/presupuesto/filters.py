import django_filters
from .models import ProgramaPresupuestario, ProyectoPresupuestario, ActividadPresupuestaria, LineaPresupuestaria


class ProgramaPresupuestarioFilter(django_filters.FilterSet):
    class Meta:
        model = ProgramaPresupuestario
        fields = {
            'codigo': ['exact', 'icontains'],
            'nombre': ['icontains'],
            'gestion': ['exact'],
            'ue_responsable': ['exact'],
            'activo': ['exact'],
        }


class ProyectoPresupuestarioFilter(django_filters.FilterSet):
    class Meta:
        model = ProyectoPresupuestario
        fields = {
            'codigo': ['exact', 'icontains'],
            'nombre': ['icontains'],
            'programa': ['exact'],
            'gestion': ['exact'],
            'activo': ['exact'],
        }


class ActividadPresupuestariaFilter(django_filters.FilterSet):
    class Meta:
        model = ActividadPresupuestaria
        fields = {
            'codigo': ['exact', 'icontains'],
            'nombre': ['icontains'],
            'proyecto': ['exact'],
            'gestion': ['exact'],
            'activo': ['exact'],
        }


class LineaPresupuestariaFilter(django_filters.FilterSet):
    class Meta:
        model = LineaPresupuestaria
        fields = {
            'gestion': ['exact'],
            'entidad': ['exact'],
            'da': ['exact'],
            'ue': ['exact'],
            'programa': ['exact'],
            'proyecto': ['exact'],
            'actividad': ['exact'],
            'finalidad_funcion': ['exact'],
            'fuente': ['exact'],
            'organismo': ['exact'],
            'objeto_gasto': ['exact'],
            'entidad_transferencia': ['exact'],
            'operacion': ['exact'],
            'version': ['exact'],
            'activo': ['exact'],
            'importe': ['gte', 'lte'],
        }
