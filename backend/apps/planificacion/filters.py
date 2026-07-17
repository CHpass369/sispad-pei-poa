import django_filters
from .models import Plan, Sector, NodoPlanificacion, AccionMedianoPlazo, AccionCortoPlazo, ArticulacionPlanificacion, PlanVersion


class PlanFilter(django_filters.FilterSet):
    class Meta:
        model = Plan
        fields = {
            'codigo': ['exact', 'icontains'],
            'nombre': ['icontains'],
            'tipo': ['exact'],
            'gestion_inicio': ['exact', 'lte', 'gte'],
            'gestion_fin': ['exact', 'lte', 'gte'],
            'activo': ['exact'],
        }


class SectorFilter(django_filters.FilterSet):
    class Meta:
        model = Sector
        fields = {
            'codigo': ['exact'],
            'nombre': ['icontains'],
            'activo': ['exact'],
        }


class NodoPlanificacionFilter(django_filters.FilterSet):
    class Meta:
        model = NodoPlanificacion
        fields = {
            'plan': ['exact'],
            'padre': ['exact'],
            'nivel': ['exact'],
            'codigo': ['exact', 'icontains'],
            'gestion': ['exact'],
            'activo': ['exact'],
        }


class AccionMedianoPlazoFilter(django_filters.FilterSet):
    class Meta:
        model = AccionMedianoPlazo
        fields = {
            'nodo_planificacion': ['exact'],
            'codigo': ['exact', 'icontains'],
            'gestion_inicio': ['exact', 'lte', 'gte'],
            'gestion_fin': ['exact', 'lte', 'gte'],
            'responsable': ['exact'],
            'activo': ['exact'],
        }


class AccionCortoPlazoFilter(django_filters.FilterSet):
    class Meta:
        model = AccionCortoPlazo
        fields = {
            'accion_mediano_plazo': ['exact'],
            'unidad_responsable': ['exact'],
            'codigo': ['exact', 'icontains'],
            'gestion': ['exact'],
            'activo': ['exact'],
        }


class ArticulacionPlanificacionFilter(django_filters.FilterSet):
    class Meta:
        model = ArticulacionPlanificacion
        fields = {
            'nodo_origen': ['exact'],
            'nodo_destino': ['exact'],
            'gestion': ['exact'],
            'es_principal': ['exact'],
        }


class PlanVersionFilter(django_filters.FilterSet):
    class Meta:
        model = PlanVersion
        fields = {
            'plan': ['exact'],
            'version_number': ['exact'],
            'status': ['exact'],
            'valid_from': ['exact', 'lte', 'gte'],
        }
