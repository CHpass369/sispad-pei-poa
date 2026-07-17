import django_filters
from .models import ReporteSeguimiento, EntradaSeguimiento, Alerta, UmbralConfiguracion


class ReporteSeguimientoFilter(django_filters.FilterSet):
    class Meta:
        model = ReporteSeguimiento
        fields = {
            'gestion': ['exact'],
            'periodo': ['exact', 'icontains'],
            'unidad_organizacional': ['exact'],
            'estado': ['exact'],
            'submitted_by': ['exact'],
            'approved_by': ['exact'],
        }


class EntradaSeguimientoFilter(django_filters.FilterSet):
    class Meta:
        model = EntradaSeguimiento
        fields = {
            'reporte': ['exact'],
            'actividad': ['exact'],
            'porcentaje_avance_fisico': ['gte', 'lte'],
            'porcentaje_avance_financiero': ['gte', 'lte'],
            'desviacion': ['gte', 'lte'],
        }


class AlertaFilter(django_filters.FilterSet):
    class Meta:
        model = Alerta
        fields = {
            'entrada': ['exact'],
            'tipo': ['exact'],
            'severidad': ['exact'],
            'activa': ['exact'],
            'resuelta_por': ['exact'],
        }


class UmbralConfiguracionFilter(django_filters.FilterSet):
    class Meta:
        model = UmbralConfiguracion
        fields = {
            'tipo_umbral': ['exact'],
            'activo': ['exact'],
        }
