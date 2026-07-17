from rest_framework import serializers
from .models import TechoPresupuestario, DistribucionTecho, MovimientoTecho


class TechoPresupuestarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = TechoPresupuestario
        fields = '__all__'


class DistribucionTechoSerializer(serializers.ModelSerializer):
    class Meta:
        model = DistribucionTecho
        fields = '__all__'


class MovimientoTechoSerializer(serializers.ModelSerializer):
    class Meta:
        model = MovimientoTecho
        fields = '__all__'
