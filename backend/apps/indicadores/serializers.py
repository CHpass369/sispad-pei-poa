from rest_framework import serializers
from .models import (
    Indicador, MetaProgramada, Operacion, Tarea,
    Producto, MedioVerificacion, Supuesto
)
from apps.core.validators import validar_meta_no_negativa


class IndicadorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Indicador
        fields = '__all__'

    def validate(self, data):
        tipo = data.get('tipo_comportamiento', getattr(self.instance, 'tipo_comportamiento', None))
        meta = data.get('meta_anual', getattr(self.instance, 'meta_anual', None))

        if tipo == 'porcentaje' and meta is not None:
            if meta < 0 or meta > 100:
                raise serializers.ValidationError(
                    {'meta_anual': 'Para indicadores de tipo porcentaje, la meta debe estar entre 0 y 100.'}
                )

        if tipo == 'cualitativo' and meta is not None and meta != 0:
            raise serializers.ValidationError(
                {'meta_anual': 'Los indicadores cualitativos no deben tener meta numérica.'}
            )

        if tipo == 'acumulable' and meta is not None:
            result = validar_meta_no_negativa(meta)
            if not result['valido']:
                raise serializers.ValidationError({'meta_anual': result['mensaje']})

        return data


class MetaProgramadaSerializer(serializers.ModelSerializer):
    class Meta:
        model = MetaProgramada
        fields = '__all__'

    def validate(self, data):
        meta_anual = data.get('meta_anual')
        t1 = data.get('trimestre1')
        t2 = data.get('trimestre2')
        t3 = data.get('trimestre3')
        t4 = data.get('trimestre4')

        trimestres = [t for t in [t1, t2, t3, t4] if t is not None]
        if trimestres and meta_anual is not None:
            from decimal import Decimal
            suma = sum(Decimal(str(t)) for t in trimestres)
            if suma != Decimal(str(meta_anual)):
                raise serializers.ValidationError(
                    f'La suma de trimestres ({suma}) debe coincidir con '
                    f'la meta anual ({meta_anual}).'
                )

        if meta_anual is not None:
            result = validar_meta_no_negativa(meta_anual)
            if not result['valido']:
                raise serializers.ValidationError({'meta_anual': result['mensaje']})

        return data


class OperacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Operacion
        fields = '__all__'

    def validate(self, data):
        fecha_inicio = data.get('fecha_inicio', getattr(self.instance, 'fecha_inicio', None))
        fecha_fin = data.get('fecha_fin', getattr(self.instance, 'fecha_fin', None))
        if fecha_inicio and fecha_fin and fecha_inicio >= fecha_fin:
            raise serializers.ValidationError(
                'La fecha de inicio debe ser anterior a la fecha de fin.'
            )
        return data


class TareaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tarea
        fields = '__all__'


class ProductoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Producto
        fields = '__all__'


class MedioVerificacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = MedioVerificacion
        fields = '__all__'


class SupuestoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supuesto
        fields = '__all__'
