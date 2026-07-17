from rest_framework import serializers
from .models import (
    ReporteSeguimiento, EntradaSeguimiento, Alerta, UmbralConfiguracion,
)
from .services import (
    calcular_eficacia_fisica, calcular_ejecucion_financiera,
    calcular_eficiencia, calcular_desviacion, calcular_proyeccion_cierre,
    determinar_semaforo,
)


class ReporteSeguimientoSerializer(serializers.ModelSerializer):
    unidad_organizacional_nombre = serializers.CharField(
        source='unidad_organizacional.nombre', read_only=True
    )
    submitted_by_email = serializers.EmailField(
        source='submitted_by.email', read_only=True, allow_null=True
    )
    approved_by_email = serializers.EmailField(
        source='approved_by.email', read_only=True, allow_null=True
    )

    class Meta:
        model = ReporteSeguimiento
        fields = [
            'id', 'gestion', 'periodo', 'unidad_organizacional',
            'unidad_organizacional_nombre', 'estado',
            'submitted_at', 'approved_at',
            'submitted_by', 'submitted_by_email',
            'approved_by', 'approved_by_email',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'created_at', 'updated_at',
            'submitted_at', 'approved_at',
        ]


class EntradaSeguimientoSerializer(serializers.ModelSerializer):
    actividad_codigo = serializers.CharField(
        source='actividad.codigo', read_only=True
    )
    actividad_nombre = serializers.CharField(
        source='actividad.nombre', read_only=True
    )
    eficacia_fisica = serializers.SerializerMethodField()
    ejecucion_financiera_pct = serializers.SerializerMethodField()
    eficiencia = serializers.SerializerMethodField()
    desviacionCalculada = serializers.SerializerMethodField()
    proyeccion = serializers.SerializerMethodField()
    semaforo = serializers.SerializerMethodField()

    class Meta:
        model = EntradaSeguimiento
        fields = [
            'id', 'reporte', 'actividad',
            'actividad_codigo', 'actividad_nombre',
            'programado_fisico', 'ejecutado_fisico',
            'porcentaje_avance_fisico',
            'presupuesto_inicial', 'presupuesto_actual',
            'programado_financiero', 'ejecutado_financiero',
            'porcentaje_avance_financiero',
            'desviacion', 'causa_desviacion',
            'accion_correctiva', 'proyeccion_cierre',
            'evidencia',
            'eficacia_fisica', 'ejecucion_financiera_pct',
            'eficiencia', 'desviacionCalculada',
            'proyeccion', 'semaforo',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'created_at', 'updated_at',
        ]

    def get_eficacia_fisica(self, obj):
        return round(calcular_eficacia_fisica(obj), 2)

    def get_ejecucion_financiera_pct(self, obj):
        return round(calcular_ejecucion_financiera(obj), 2)

    def get_eficiencia(self, obj):
        return round(calcular_eficiencia(obj), 2)

    def get_desviacionCalculada(self, obj):
        return round(calcular_desviacion(obj), 2)

    def get_proyeccion(self, obj):
        return calcular_proyeccion_cierre(obj)

    def get_semaforo(self, obj):
        return determinar_semaforo(obj.porcentaje_avance_fisico)


class EntradaSeguimientoListSerializer(serializers.ModelSerializer):
    """Serializer liviano para listados sin campos calculados."""
    actividad_codigo = serializers.CharField(
        source='actividad.codigo', read_only=True
    )
    actividad_nombre = serializers.CharField(
        source='actividad.nombre', read_only=True
    )
    semaforo = serializers.SerializerMethodField()

    class Meta:
        model = EntradaSeguimiento
        fields = [
            'id', 'reporte', 'actividad',
            'actividad_codigo', 'actividad_nombre',
            'porcentaje_avance_fisico',
            'porcentaje_avance_financiero',
            'semaforo',
        ]

    def get_semaforo(self, obj):
        return determinar_semaforo(obj.porcentaje_avance_fisico)


class AlertaSerializer(serializers.ModelSerializer):
    entrada_actividad = serializers.CharField(
        source='entrada.actividad.nombre', read_only=True
    )
    tipo_display = serializers.CharField(
        source='get_tipo_display', read_only=True
    )
    severidad_display = serializers.CharField(
        source='get_severidad_display', read_only=True
    )
    resuelta_por_email = serializers.EmailField(
        source='resuelta_por.email', read_only=True, allow_null=True
    )

    class Meta:
        model = Alerta
        fields = [
            'id', 'entrada', 'entrada_actividad',
            'tipo', 'tipo_display',
            'severidad', 'severidad_display',
            'mensaje', 'activa',
            'resuelta_en', 'resuelta_por', 'resuelta_por_email',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'created_at', 'updated_at',
            'resuelta_en', 'resuelta_por',
        ]


class UmbralConfiguracionSerializer(serializers.ModelSerializer):
    tipo_umbral_display = serializers.CharField(
        source='get_tipo_umbral_display', read_only=True
    )

    class Meta:
        model = UmbralConfiguracion
        fields = [
            'id', 'tipo_umbral', 'tipo_umbral_display',
            'porcentaje_minimo', 'porcentaje_maximo',
            'activo', 'descripcion',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']
