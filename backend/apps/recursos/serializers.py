from rest_framework import serializers
from .models import EstimacionRecurso, EstimacionPlurianual


class EstimacionRecursoSerializer(serializers.ModelSerializer):
    class Meta:
        model = EstimacionRecurso
        fields = '__all__'


class EstimacionPlurianualSerializer(serializers.ModelSerializer):
    class Meta:
        model = EstimacionPlurianual
        fields = '__all__'
