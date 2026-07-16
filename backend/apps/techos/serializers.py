from rest_framework import serializers
from .models import TechoPresupuestario, DistribucionTecho


class TechoPresupuestarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = TechoPresupuestario
        fields = '__all__'


class DistribucionTechoSerializer(serializers.ModelSerializer):
    class Meta:
        model = DistribucionTecho
        fields = '__all__'
