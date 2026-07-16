from rest_framework import serializers
from .models import (
    Indicador, MetaProgramada, Operacion, Tarea,
    Producto, MedioVerificacion, Supuesto
)


class IndicadorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Indicador
        fields = '__all__'


class MetaProgramadaSerializer(serializers.ModelSerializer):
    class Meta:
        model = MetaProgramada
        fields = '__all__'


class OperacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Operacion
        fields = '__all__'


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
