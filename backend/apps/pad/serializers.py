from rest_framework import serializers

from .models import SectorPAD


class SectorPADSerializer(serializers.ModelSerializer):
    class Meta:
        model = SectorPAD
        fields = '__all__'
