from rest_framework import serializers
from .models import EventoAuditoria


class EventoAuditoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventoAuditoria
        fields = '__all__'
        read_only_fields = ['creado_en']
