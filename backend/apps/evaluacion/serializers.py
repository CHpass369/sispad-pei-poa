from rest_framework import serializers
from .models import (
    Evaluacion, CriterioEvaluacion, ResultadoEvaluacion,
    LeccionAprendida, Recomendacion,
)


class CriterioEvaluacionSerializer(serializers.ModelSerializer):
    weighted_score = serializers.DecimalField(
        max_digits=10, decimal_places=4, read_only=True,
    )

    class Meta:
        model = CriterioEvaluacion
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class ResultadoEvaluacionSerializer(serializers.ModelSerializer):
    poau_codigo = serializers.CharField(source='poau.codigo', read_only=True, default=None)
    unidad_nombre = serializers.CharField(source='unidad.nombre', read_only=True, default=None)
    resultado_pad_codigo = serializers.CharField(
        source='resultado_pad.codigo', read_only=True, default=None,
    )

    class Meta:
        model = ResultadoEvaluacion
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class LeccionAprendidaSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeccionAprendida
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class RecomendacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recomendacion
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class EvaluacionListSerializer(serializers.ModelSerializer):
    plan_nombre = serializers.CharField(source='plan.nombre', read_only=True)
    plan_tipo = serializers.CharField(source='plan.get_tipo_display', read_only=True)
    total_criterios = serializers.IntegerField(read_only=True, default=0)
    total_resultados = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = Evaluacion
        fields = [
            'id', 'plan', 'plan_nombre', 'plan_tipo',
            'fiscal_year', 'evaluation_type', 'period',
            'status', 'responsible_team',
            'total_criterios', 'total_resultados',
            'created_at', 'updated_at',
        ]


class EvaluacionSerializer(serializers.ModelSerializer):
    criterios = CriterioEvaluacionSerializer(many=True, read_only=True)
    resultados = ResultadoEvaluacionSerializer(many=True, read_only=True)
    lecciones = LeccionAprendidaSerializer(many=True, read_only=True)
    recomendaciones = RecomendacionSerializer(many=True, read_only=True)
    plan_nombre = serializers.CharField(source='plan.nombre', read_only=True)

    class Meta:
        model = Evaluacion
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by', 'updated_by']
