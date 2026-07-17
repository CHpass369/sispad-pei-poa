import django_filters
from .models import (
    SectorPAD, PoliticaPAD, LineamientoEstrategico, ResultadoTerritorial,
    ArticulacionLog, ProductoTerritorial, ProgramacionAnualPAD, ArticulacionSIPEB,
)


class SectorPADFilter(django_filters.FilterSet):
    class Meta:
        model = SectorPAD
        fields = {
            'codigo': ['exact'],
            'nombre': ['icontains'],
        }


class PoliticaPADFilter(django_filters.FilterSet):
    class Meta:
        model = PoliticaPAD
        fields = {
            'codigo': ['exact', 'icontains'],
            'nombre': ['icontains'],
            'gestion': ['exact'],
        }


class LineamientoEstrategicoFilter(django_filters.FilterSet):
    class Meta:
        model = LineamientoEstrategico
        fields = {
            'codigo': ['exact', 'icontains'],
            'nombre': ['icontains'],
            'politica': ['exact'],
            'gestion': ['exact'],
        }


class ResultadoTerritorialFilter(django_filters.FilterSet):
    class Meta:
        model = ResultadoTerritorial
        fields = {
            'codigo': ['exact', 'icontains'],
            'nombre': ['icontains'],
            'lineamiento': ['exact'],
            'sector': ['exact'],
            'gestion': ['exact'],
            'estado': ['exact'],
            'cod_geografico': ['exact', 'icontains'],
        }


class ArticulacionLogFilter(django_filters.FilterSet):
    class Meta:
        model = ArticulacionLog
        fields = {
            'entidad': ['exact'],
            'entidad_id': ['exact'],
            'accion': ['exact'],
            'usuario': ['exact'],
        }


class ProductoTerritorialFilter(django_filters.FilterSet):
    class Meta:
        model = ProductoTerritorial
        fields = {
            'codigo': ['exact', 'icontains'],
            'nombre': ['icontains'],
            'resultado': ['exact'],
            'gestion': ['exact'],
            'cuenta_con_financiamiento': ['exact'],
        }


class ProgramacionAnualPADFilter(django_filters.FilterSet):
    class Meta:
        model = ProgramacionAnualPAD
        fields = {
            'resultado': ['exact'],
            'producto': ['exact'],
            'anio': ['exact', 'gte', 'lte'],
            'tipo': ['exact'],
        }


class ArticulacionSIPEBFilter(django_filters.FilterSet):
    class Meta:
        model = ArticulacionSIPEB
        fields = {
            'resultado': ['exact'],
            'gestion': ['exact'],
            'cod_eje_pgdesa': ['exact', 'icontains'],
            'cod_ods': ['exact'],
            'cod_sector': ['exact'],
        }
