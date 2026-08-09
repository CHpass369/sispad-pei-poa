from decimal import Decimal
from rest_framework import serializers
from .models import ProgramaPresupuestario, ProyectoPresupuestario, ActividadPresupuestaria, LineaPresupuestaria
from apps.core.validators import validar_meta_no_negativa, validar_nombre_corto


def _validar_nombre(self, data, etiqueta):
    nombre = data.get('nombre') or getattr(self.instance, 'nombre', None)
    mensaje = validar_nombre_corto(nombre, etiqueta)
    if mensaje:
        raise serializers.ValidationError({'nombre': mensaje})
    return data


class ProgramaPresupuestarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProgramaPresupuestario
        fields = '__all__'

    def validate(self, data):
        return _validar_nombre(self, data, 'del programa')


class ProyectoPresupuestarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProyectoPresupuestario
        fields = '__all__'

    def validate(self, data):
        return _validar_nombre(self, data, 'del proyecto')


class ActividadPresupuestariaSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActividadPresupuestaria
        fields = '__all__'

    def validate(self, data):
        return _validar_nombre(self, data, 'de la actividad')


class LineaPresupuestariaSerializer(serializers.ModelSerializer):
    class Meta:
        model = LineaPresupuestaria
        fields = '__all__'

    def validate_importe(self, value):
        result = validar_meta_no_negativa(value)
        if not result['valido']:
            raise serializers.ValidationError(result['mensaje'])
        return value

    def validate(self, data):
        importe = data.get('importe', getattr(self.instance, 'importe', None))
        importe_plurianual = data.get('importe_plurianual', getattr(self.instance, 'importe_plurianual', None))
        importe_gestion_anterior = data.get('importe_gestion_anterior', getattr(self.instance, 'importe_gestion_anterior', None))

        if importe is not None and importe < 0:
            raise serializers.ValidationError(
                {'importe': 'El importe no puede ser negativo.'}
            )

        if importe_plurianual is not None and importe is not None:
            if importe_plurianual > importe * 3:
                raise serializers.ValidationError(
                    {'importe_plurianual': (
                        f'El importe plurianual (Bs {importe_plurianual}) '
                        f'no puede exceder 3 veces el importe anual (Bs {importe}).'
                    )}
                )

        if importe_gestion_anterior is not None and importe_gestion_anterior < 0:
            raise serializers.ValidationError(
                {'importe_gestion_anterior': 'El importe de gestión anterior no puede ser negativo.'}
            )

        return data
