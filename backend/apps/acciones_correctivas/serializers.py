from rest_framework import serializers
from .models import AccionCorrectiva, CompromisoAccionCorrectiva


class CompromisoAccionCorrectivaSerializer(serializers.ModelSerializer):
    esta_vencido = serializers.BooleanField(read_only=True)

    class Meta:
        model = CompromisoAccionCorrectiva
        fields = '__all__'
        read_only_fields = [
            'id', 'created_at', 'updated_at',
            'created_by', 'updated_by', 'completed_at',
        ]


class CompromisoAccionCorrectivaListSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompromisoAccionCorrectiva
        fields = [
            'id', 'description', 'due_date', 'status',
            'completed_at', 'notes',
        ]


class AccionCorrectivaListSerializer(serializers.ModelSerializer):
    responsible_email = serializers.CharField(
        source='responsible.email', read_only=True,
    )
    responsible_unit_nombre = serializers.CharField(
        source='responsible_unit.nombre', read_only=True, default=None,
    )
    total_compromisos = serializers.IntegerField(read_only=True, default=0)
    compromisos_cumplidos = serializers.IntegerField(read_only=True, default=0)
    porcentaje_cumplimiento = serializers.FloatField(read_only=True, default=0)
    esta_vencida = serializers.BooleanField(read_only=True)

    class Meta:
        model = AccionCorrectiva
        fields = [
            'id', 'description', 'cause', 'responsible', 'responsible_email',
            'responsible_unit', 'responsible_unit_nombre',
            'start_date', 'due_date', 'status', 'gestion',
            'total_compromisos', 'compromisos_cumplidos',
            'porcentaje_cumplimiento', 'esta_vencida',
            'created_at', 'updated_at',
        ]


class AccionCorrectivaSerializer(serializers.ModelSerializer):
    compromisos = CompromisoAccionCorrectivaSerializer(many=True, read_only=True)
    responsible_email = serializers.CharField(
        source='responsible.email', read_only=True,
    )
    responsible_unit_nombre = serializers.CharField(
        source='responsible_unit.nombre', read_only=True, default=None,
    )
    verified_by_email = serializers.CharField(
        source='verified_by.email', read_only=True, default=None,
    )
    alerta_descripcion = serializers.CharField(
        source='alerta.descripcion', read_only=True, default=None,
    )
    esta_vencida = serializers.BooleanField(read_only=True)
    porcentaje_cumplimiento = serializers.FloatField(read_only=True)

    class Meta:
        model = AccionCorrectiva
        fields = '__all__'
        read_only_fields = [
            'id', 'created_at', 'updated_at',
            'created_by', 'updated_by',
            'verified_by', 'verified_at',
        ]
