from rest_framework import serializers
from .models import Plan, NodoPlanificacion, AccionMedianoPlazo, AccionCortoPlazo, ArticulacionPlanificacion


class PlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plan
        fields = '__all__'


class NodoPlanificacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = NodoPlanificacion
        fields = '__all__'


class AccionMedianoPlazoSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccionMedianoPlazo
        fields = '__all__'


class AccionCortoPlazoSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccionCortoPlazo
        fields = '__all__'


class ArticulacionPlanificacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ArticulacionPlanificacion
        fields = '__all__'
