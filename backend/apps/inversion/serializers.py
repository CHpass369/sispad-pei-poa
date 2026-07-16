from rest_framework import serializers
from .models import ProyectoInversion, ProgramacionPlurianualProyecto, ProgramacionFisicaFinanciera


class ProyectoInversionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProyectoInversion
        fields = '__all__'


class ProgramacionPlurianualProyectoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProgramacionPlurianualProyecto
        fields = '__all__'


class ProgramacionFisicaFinancieraSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProgramacionFisicaFinanciera
        fields = '__all__'
