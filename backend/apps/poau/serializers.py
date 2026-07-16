from rest_framework import serializers
from .models import POAU, POAUActividad, EjecucionFisica, EjecucionFinanciera
from apps.planificacion.models import AccionCortoPlazo


class POAUActividadSerializer(serializers.ModelSerializer):
    meta_q1 = serializers.DecimalField(
        max_digits=20, decimal_places=4, required=False, allow_null=True,
    )
    meta_q2 = serializers.DecimalField(
        max_digits=20, decimal_places=4, required=False, allow_null=True,
    )
    meta_q3 = serializers.DecimalField(
        max_digits=20, decimal_places=4, required=False, allow_null=True,
    )
    meta_q4 = serializers.DecimalField(
        max_digits=20, decimal_places=4, required=False, allow_null=True,
    )
    accion_corto_plazo = serializers.PrimaryKeyRelatedField(
        queryset=AccionCortoPlazo.objects.all(),
        required=False, allow_null=True,
    )
    avance = serializers.SerializerMethodField()

    class Meta:
        model = POAUActividad
        fields = '__all__'
        read_only_fields = ['id', 'avance']

    def validate_meta_q1(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError('Meta Q1 no puede ser negativa')
        return value

    def validate_meta_q2(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError('Meta Q2 no puede ser negativa')
        return value

    def validate_meta_q3(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError('Meta Q3 no puede ser negativa')
        return value

    def validate_meta_q4(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError('Meta Q4 no puede ser negativa')
        return value

    def validate(self, attrs):
        trimestres = [
            attrs.get('meta_q1'),
            attrs.get('meta_q2'),
            attrs.get('meta_q3'),
            attrs.get('meta_q4'),
        ]
        meta_anual = attrs.get('meta_fisica_anual')

        if all(t is not None for t in trimestres) and meta_anual is not None:
            suma = sum(trimestres)
            if suma != meta_anual:
                raise serializers.ValidationError(
                    f'La suma de trimestres ({suma}) debe coincidir con '
                    f'la meta anual ({meta_anual})'
                )
        return attrs

    def get_avance(self, obj) -> float:
        ef_qs = obj.ejecucion_fisica.filter(tipo_periodo='trimestral')
        total_programado = sum(
            (ef.programado or 0) for ef in ef_qs
        )
        total_ejecutado = sum(
            (ef.ejecutado or 0) for ef in ef_qs
        )
        if total_programado:
            return round(float(total_ejecutado / total_programado * 100), 2)
        return 0.0

    def _sincronizar_ejecucion_fisica(self, actividad):
        gestion = actividad.poau.gestion
        trimestres = [
            ('Q1', actividad.meta_q1),
            ('Q2', actividad.meta_q2),
            ('Q3', actividad.meta_q3),
            ('Q4', actividad.meta_q4),
        ]
        for q, valor in trimestres:
            if valor is not None:
                periodo = f'{gestion}-{q}'
                EjecucionFisica.objects.update_or_create(
                    actividad=actividad,
                    periodo=periodo,
                    defaults={
                        'programado': valor,
                        'tipo_periodo': 'trimestral',
                    },
                )

    def create(self, validated_data):
        actividad = super().create(validated_data)
        self._sincronizar_ejecucion_fisica(actividad)
        return actividad

    def update(self, instance, validated_data):
        actividad = super().update(instance, validated_data)
        self._sincronizar_ejecucion_fisica(actividad)
        return actividad


class POAUListSerializer(serializers.ModelSerializer):
    """Serializer liviano para listados de POAU"""
    unidad_nombre = serializers.CharField(
        source='unidad.nombre', read_only=True,
    )
    responsable_nombre = serializers.SerializerMethodField()

    class Meta:
        model = POAU
        fields = [
            'id', 'codigo', 'nombre', 'unidad', 'unidad_nombre',
            'gestion', 'estado', 'responsable', 'responsable_nombre',
            'created_at', 'updated_at',
        ]

    def get_responsable_nombre(self, obj):
        if obj.responsable:
            return obj.responsable.get_full_name() or obj.responsable.email
        return None


class POAUSerializer(serializers.ModelSerializer):
    actividades = POAUActividadSerializer(many=True, read_only=True)

    class Meta:
        model = POAU
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class EjecucionFisicaSerializer(serializers.ModelSerializer):
    class Meta:
        model = EjecucionFisica
        fields = '__all__'
        read_only_fields = ['id']


class EjecucionFinancieraSerializer(serializers.ModelSerializer):
    class Meta:
        model = EjecucionFinanciera
        fields = '__all__'
        read_only_fields = ['id']
