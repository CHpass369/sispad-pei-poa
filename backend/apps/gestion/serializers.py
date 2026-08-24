from rest_framework import serializers
from .models import GestionFiscal, CicloFormulacion, EtapaFormulacion


class GestionFiscalSerializer(serializers.ModelSerializer):
    """Contrato V1 de la gestión fiscal.

    `estado` y `activa` son de solo lectura: el candado de SIS-POA (ADR-007)
    lo mueven únicamente `habilitar_gestion`/`cerrar_gestion`, que validan la
    transición y dejan rastro en `EventoAuditoria`. Hasta este cambio un
    `PATCH {"estado": "abierta"}` acá saltaba las tres cosas.
    """

    estado_display = serializers.CharField(source='get_estado_display', read_only=True)

    class Meta:
        model = GestionFiscal
        fields = '__all__'
        read_only_fields = [
            'creado_en', 'actualizado_en', 'estado', 'estado_display', 'activa',
            'fecha_apertura', 'fecha_cierre',
        ]


class CicloFormulacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = CicloFormulacion
        fields = '__all__'


class EtapaFormulacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = EtapaFormulacion
        fields = '__all__'
