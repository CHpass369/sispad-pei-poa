from decimal import Decimal
from rest_framework import serializers
from .models import ProgramaPresupuestario, ProyectoPresupuestario, ActividadPresupuestaria, LineaPresupuestaria
from apps.core.validators import validar_meta_no_negativa


class ProgramaPresupuestarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProgramaPresupuestario
        fields = '__all__'

    def validate(self, data):
        nombre = data.get('nombre') or getattr(self.instance, 'nombre', None)
        if nombre and len(nombre.strip()) < 3:
            raise serializers.ValidationError({'nombre': 'El nombre del programa es demasiado corto.'})
        return data


class ProyectoPresupuestarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProyectoPresupuestario
        fields = '__all__'

    def validate(self, data):
        nombre = data.get('nombre') or getattr(self.instance, 'nombre', None)
        if nombre and len(nombre.strip()) < 3:
            raise serializers.ValidationError({'nombre': 'El nombre del proyecto es demasiado corto.'})
        return data


class ActividadPresupuestariaSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActividadPresupuestaria
        fields = '__all__'

    def validate(self, data):
        nombre = data.get('nombre') or getattr(self.instance, 'nombre', None)
        if nombre and len(nombre.strip()) < 3:
            raise serializers.ValidationError({'nombre': 'El nombre de la actividad es demasiado corto.'})
        return data


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
