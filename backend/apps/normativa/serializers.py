from rest_framework import serializers
from .models import VersionNormativa, ReglaPresupuestariaLegal


class VersionNormativaSerializer(serializers.ModelSerializer):
    class Meta:
        model = VersionNormativa
        fields = '__all__'


class ReglaPresupuestariaLegalSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReglaPresupuestariaLegal
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']
