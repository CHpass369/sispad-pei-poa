from rest_framework import serializers
from .models import SolicitudModificacion, CambioModificacion, ImpactoModificacion


class CambioModificacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = CambioModificacion
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by', 'updated_by']


class ImpactoModificacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImpactoModificacion
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by', 'updated_by']


class SolicitudModificacionListSerializer(serializers.ModelSerializer):
    solicitado_por_nombre = serializers.SerializerMethodField()
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)

    class Meta:
        model = SolicitudModificacion
        fields = [
            'id', 'tipo', 'tipo_display', 'gestion_fiscal',
            'entidad_afectada_tipo', 'entidad_afectada_id',
            'poau', 'motivo', 'solicitado_por', 'solicitado_por_nombre',
            'estado', 'estado_display', 'fecha_efectiva', 'version',
            'created_at', 'updated_at',
        ]

    def get_solicitado_por_nombre(self, obj):
        if obj.solicitado_por:
            return obj.solicitado_por.get_full_name() or obj.solicitado_por.email
        return None


class SolicitudModificacionSerializer(serializers.ModelSerializer):
    cambios = CambioModificacionSerializer(many=True, read_only=True)
    impacto = ImpactoModificacionSerializer(read_only=True)
    solicitado_por_nombre = serializers.SerializerMethodField()
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)

    cambios_crear = CambioModificacionSerializer(many=True, write_only=True, required=False)

    class Meta:
        model = SolicitudModificacion
        fields = [
            'id', 'tipo', 'tipo_display', 'gestion_fiscal',
            'entidad_afectada_tipo', 'entidad_afectada_id',
            'poau', 'motivo', 'informe_tecnico', 'documento_legal',
            'solicitado_por', 'solicitado_por_nombre',
            'estado', 'estado_display', 'fecha_efectiva', 'observaciones',
            'version', 'cambios', 'cambios_crear', 'impacto',
            'created_at', 'updated_at', 'created_by', 'updated_by',
        ]
        read_only_fields = [
            'id', 'version', 'created_at', 'updated_at',
            'created_by', 'updated_by',
        ]

    def get_solicitado_por_nombre(self, obj):
        if obj.solicitado_por:
            return obj.solicitado_por.get_full_name() or obj.solicitado_por.email
        return None

    def create(self, validated_data):
        cambios_data = validated_data.pop('cambios_crear', [])
        solicitud = SolicitudModificacion.objects.create(**validated_data)
        for cambio_data in cambios_data:
            CambioModificacion.objects.create(solicitud=solicitud, **cambio_data)
        return solicitud

    def update(self, instance, validated_data):
        cambios_data = validated_data.pop('cambios_crear', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if cambios_data is not None:
            instance.cambios.all().delete()
            for cambio_data in cambios_data:
                CambioModificacion.objects.create(solicitud=instance, **cambio_data)
        return instance
