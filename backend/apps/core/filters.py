import django_filters

from django.utils import timezone


class BaseFilterSet(django_filters.FilterSet):
    gestion = django_filters.NumberFilter(field_name='gestion')
    gestion_min = django_filters.NumberFilter(field_name='gestion', lookup_expr='gte')
    gestion_max = django_filters.NumberFilter(field_name='gestion', lookup_expr='lte')
    estado = django_filters.CharFilter(field_name='estado', lookup_expr='exact')
    fecha_creacion_desde = django_filters.DateTimeFilter(
        field_name='created_at', lookup_expr='gte'
    )
    fecha_creacion_hasta = django_filters.DateTimeFilter(
        field_name='created_at', lookup_expr='lte'
    )
    search = django_filters.CharFilter(method='filter_search')

    class Meta:
        abstract = True

    def filter_search(self, queryset, name, value):
        if not value:
            return queryset
        return queryset


class PlanFilter(BaseFilterSet):
    tipo = django_filters.CharFilter(field_name='tipo', lookup_expr='exact')
    unidad_ejecutora = django_filters.UUIDFilter(field_name='nodos__acciones_mediano_plazo__acciones_corto_plazo__unidad_responsable__id')
    gestion_inicio_min = django_filters.NumberFilter(field_name='gestion_inicio', lookup_expr='gte')
    gestion_fin_max = django_filters.NumberFilter(field_name='gestion_fin', lookup_expr='lte')

    class Meta:
        fields = ['gestion', 'estado', 'tipo', 'unidad_ejecutora']


class POAUFilter(BaseFilterSet):
    unidad_ejecutora = django_filters.UUIDFilter(field_name='unidad__id')
    semaforo = django_filters.CharFilter(method='filter_semaforo')
    codigo = django_filters.CharFilter(field_name='codigo', lookup_expr='icontains')
    nombre = django_filters.CharFilter(field_name='nombre', lookup_expr='icontains')
    responsable = django_filters.UUIDFilter(field_name='responsable__id')

    class Meta:
        fields = ['gestion', 'estado', 'unidad_ejecutora', 'semaforo']

    def filter_semaforo(self, queryset, name, value):
        if value not in ('verde', 'amarillo', 'rojo'):
            return queryset
        from apps.poau.models import POAUActividad
        from decimal import Decimal
        threshold_map = {
            'verde': Decimal('80'),
            'amarillo': Decimal('50'),
            'rojo': Decimal('0'),
        }
        upper_map = {
            'verde': Decimal('999'),
            'amarillo': Decimal('80'),
            'rojo': Decimal('50'),
        }
        min_val = threshold_map[value]
        max_val = upper_map[value]
        actividad_ids = []
        for poau in queryset:
            total_programado = Decimal('0')
            total_ejecutado = Decimal('0')
            for act in poau.actividades.all():
                from apps.poau.models import EjecucionFisica
                for ef in EjecucionFisica.objects.filter(actividad=act):
                    total_programado += ef.programado or Decimal('0')
                    total_ejecutado += ef.ejecutado or Decimal('0')
            if total_programado > 0:
                avance = (total_ejecutado / total_programado) * 100
            else:
                avance = Decimal('0')
            if value == 'verde' and avance >= min_val:
                actividad_ids.append(poau.pk)
            elif value == 'amarillo' and min_val <= avance < max_val:
                actividad_ids.append(poau.pk)
            elif value == 'rojo' and avance < min_val:
                actividad_ids.append(poau.pk)
        return queryset.filter(pk__in=actividad_ids)


class IndicadorFilter(BaseFilterSet):
    sector = django_filters.CharFilter(method='filter_sector')
    politica = django_filters.CharFilter(method='filter_politica')
    tipo_comportamiento = django_filters.CharFilter(field_name='tipo_comportamiento', lookup_expr='exact')
    unidad_medida = django_filters.UUIDFilter(field_name='unidad_medida__id')
    nombre = django_filters.CharFilter(field_name='nombre', lookup_expr='icontains')
    codigo = django_filters.CharFilter(field_name='codigo', lookup_expr='icontains')

    class Meta:
        fields = ['gestion', 'sector', 'politica', 'tipo_comportamiento', 'unidad_medida']

    def filter_sector(self, queryset, name, value):
        return queryset.filter(
            operacion__accion_corto_plazo__accion_mediano_plazo__nodo_planificacion__plan__nodos__nivel='pilar'
        )

    def filter_politica(self, queryset, name, value):
        return queryset


class PresupuestoFilter(BaseFilterSet):
    fuente_financiamiento = django_filters.UUIDFilter(field_name='fuente__id')
    programa = django_filters.UUIDFilter(field_name='programa__id')
    ue = django_filters.UUIDFilter(field_name='ue__id')
    objeto_gasto = django_filters.UUIDFilter(field_name='objeto_gasto__id')
    importe_min = django_filters.NumberFilter(field_name='importe', lookup_expr='gte')
    importe_max = django_filters.NumberFilter(field_name='importe', lookup_expr='lte')
    version = django_filters.NumberFilter(field_name='version')

    class Meta:
        fields = ['gestion', 'fuente_financiamiento', 'programa', 'ue', 'objeto_gasto', 'version']


class AuditoriaFilter(BaseFilterSet):
    usuario = django_filters.UUIDFilter(field_name='usuario__id')
    accion = django_filters.CharFilter(field_name='accion', lookup_expr='exact')
    fecha_inicio = django_filters.DateTimeFilter(field_name='creado_en', lookup_expr='gte')
    fecha_fin = django_filters.DateTimeFilter(field_name='creado_en', lookup_expr='lte')
    modelo = django_filters.CharFilter(field_name='entidad', lookup_expr='icontains')
    entidad_id = django_filters.CharFilter(field_name='entidad_id', lookup_expr='exact')

    class Meta:
        fields = ['usuario', 'accion', 'fecha_inicio', 'fecha_fin', 'modelo']
