from django.db.models import Count, Q
from rest_framework import serializers
from .models import TipoNotificacion, Notificacion, PreferenciaNotificacion


class TipoNotificacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoNotificacion
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']


class NotificacionSerializer(serializers.ModelSerializer):
    tipo_nombre = serializers.CharField(source='tipo.nombre', read_only=True)
    tipo_codigo = serializers.CharField(source='tipo.codigo', read_only=True)

    class Meta:
        model = Notificacion
        fields = [
            'id', 'user', 'tipo', 'tipo_nombre', 'tipo_codigo',
            'titulo', 'mensaje', 'is_read', 'read_at', 'priority',
            'entity_type', 'entity_id', 'gestion', 'metadata',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'created_at', 'updated_at', 'created_by', 'updated_by',
            'read_at', 'is_read',
        ]


class ResumenNotificacionesSerializer(serializers.Serializer):
    total_no_leidas = serializers.IntegerField()
    alta = serializers.IntegerField()
    media = serializers.IntegerField()
    baja = serializers.IntegerField()


class PreferenciaNotificacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PreferenciaNotificacion
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']
