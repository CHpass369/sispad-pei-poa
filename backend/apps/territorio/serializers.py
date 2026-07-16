from rest_framework import serializers
from .models import Distrito, UnidadTerritorial, LocalizacionTerritorial


class DistritoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Distrito
        fields = '__all__'


class UnidadTerritorialSerializer(serializers.ModelSerializer):
    class Meta:
        model = UnidadTerritorial
        fields = '__all__'


class LocalizacionTerritorialSerializer(serializers.ModelSerializer):
    class Meta:
        model = LocalizacionTerritorial
        fields = '__all__'
