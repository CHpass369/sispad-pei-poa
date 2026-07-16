from rest_framework import serializers
from .models import ProgramaPresupuestario, ProyectoPresupuestario, ActividadPresupuestaria, LineaPresupuestaria


class ProgramaPresupuestarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProgramaPresupuestario
        fields = '__all__'


class ProyectoPresupuestarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProyectoPresupuestario
        fields = '__all__'


class ActividadPresupuestariaSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActividadPresupuestaria
        fields = '__all__'


class LineaPresupuestariaSerializer(serializers.ModelSerializer):
    class Meta:
        model = LineaPresupuestaria
        fields = '__all__'
