import django_filters
from .models import ProyectoInversion, ProgramacionPlurianualProyecto, ProgramacionFisicaFinanciera


class ProyectoInversionFilter(django_filters.FilterSet):
    class Meta:
        model = ProyectoInversion
        fields = {
            'codigo_interno': ['exact', 'icontains'],
            'codigo_sisin': ['exact', 'icontains'],
            'nombre': ['icontains'],
            'tipo': ['exact'],
            'prioridad': ['exact', 'lte', 'gte'],
            'etapa': ['exact'],
            'ue': ['exact'],
            'programa': ['exact'],
            'fuente': ['exact'],
            'organismo': ['exact'],
            'gestion_inicio': ['exact', 'lte', 'gte'],
            'gestion_fin': ['exact', 'lte', 'gte'],
            'activo': ['exact'],
            'costo_total': ['gte', 'lte'],
        }


class ProgramacionPlurianualProyectoFilter(django_filters.FilterSet):
    class Meta:
        model = ProgramacionPlurianualProyecto
        fields = {
            'proyecto': ['exact'],
            'anio': ['exact', 'gte', 'lte'],
            'monto_programado': ['gte', 'lte'],
        }


class ProgramacionFisicaFinancieraFilter(django_filters.FilterSet):
    class Meta:
        model = ProgramacionFisicaFinanciera
        fields = {
            'proyecto': ['exact'],
            'gestion': ['exact'],
            'monto_programado': ['gte', 'lte'],
        }
