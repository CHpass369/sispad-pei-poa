from rest_framework import serializers
from .models import GestionFiscal, CicloFormulacion, EtapaFormulacion


class GestionFiscalSerializer(serializers.ModelSerializer):
    class Meta:
        model = GestionFiscal
        fields = '__all__'
        read_only_fields = ['creado_en', 'actualizado_en']


class CicloFormulacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = CicloFormulacion
        fields = '__all__'


class EtapaFormulacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = EtapaFormulacion
        fields = '__all__'
