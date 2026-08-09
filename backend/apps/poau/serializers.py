from rest_framework import serializers
from .models import POAU, POAUActividad, EjecucionFisica, EjecucionFinanciera
from apps.planificacion.models import AccionCortoPlazo
from apps.core.validators import validar_valor_no_negativo
from apps.core.serializer_mixins import EjecucionNoNegativaMixin


def _validar_meta_trimestral(value, trimestre):
    mensaje = validar_valor_no_negativo(value, f'Meta {trimestre}')
    if mensaje:
        raise serializers.ValidationError(mensaje)
    return value


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
        return _validar_meta_trimestral(value, 'Q1')

    def validate_meta_q2(self, value):
        return _validar_meta_trimestral(value, 'Q2')

    def validate_meta_q3(self, value):
        return _validar_meta_trimestral(value, 'Q3')

    def validate_meta_q4(self, value):
        return _validar_meta_trimestral(value, 'Q4')

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

    def validate(self, data):
        instance = self.instance
        if instance and instance.estado != 'borrador':
            if self.partial:
                raise serializers.ValidationError(
                    f'No se puede modificar un POAU en estado "{instance.get_estado_display()}". '
                    f'Solo los POAUs en borrador pueden ser editados.'
                )
            else:
                raise serializers.ValidationError(
                    f'El POAU está en estado "{instance.get_estado_display()}" y no puede ser modificado.'
                )
        return data


class EjecucionFisicaSerializer(EjecucionNoNegativaMixin, serializers.ModelSerializer):
    class Meta:
        model = EjecucionFisica
        fields = '__all__'
        read_only_fields = ['id']


class EjecucionFinancieraSerializer(EjecucionNoNegativaMixin, serializers.ModelSerializer):
    class Meta:
        model = EjecucionFinanciera
        fields = '__all__'
        read_only_fields = ['id']
