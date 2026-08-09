"""Serializers V2 del kernel estratégico SIS-PE (WP-04).

Regla ADR-002: los serializers no contienen lógica compleja; los comandos de
negocio (aprobar versión, etc.) viven en el modelo o en servicios.
"""
from rest_framework import serializers

from apps.planificacion.models_v2 import (
    InstrumentoPlanificacion,
    NodoEstrategico,
    TipoInstrumento,
    TipoNodoEstrategico,
    TipoVinculoEstrategico,
    VersionInstrumento,
    VersionMetodologia,
    VinculoEstrategico,
)


class TipoInstrumentoSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoInstrumento
        fields = '__all__'
        read_only_fields = ['id', 'created_at']


class InstrumentoSerializer(serializers.ModelSerializer):
    tipo_nombre = serializers.CharField(source='tipo.nombre', read_only=True)
    versiones_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = InstrumentoPlanificacion
        fields = [
            'id', 'tipo', 'tipo_nombre', 'codigo', 'nombre',
            'institucion_responsable', 'periodo_inicio', 'periodo_fin',
            'ambito', 'descripcion', 'estado', 'versiones_count',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class VersionMetodologiaSerializer(serializers.ModelSerializer):
    class Meta:
        model = VersionMetodologia
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class VersionInstrumentoSerializer(serializers.ModelSerializer):
    instrumento_codigo = serializers.CharField(
        source='instrumento.codigo', read_only=True,
    )
    metodologia_nombre = serializers.CharField(
        source='metodologia.nombre', read_only=True,
    )
    nodos_count = serializers.IntegerField(read_only=True, default=0)
    vinculos_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = VersionInstrumento
        fields = [
            'id', 'instrumento', 'instrumento_codigo', 'numero', 'etiqueta',
            'metodologia', 'metodologia_nombre', 'estado', 'inmutable',
            'vigencia_desde', 'vigencia_hasta', 'fecha_aprobacion',
            'norma_aprobacion', 'motivo_cambio', 'checksum',
            'nodos_count', 'vinculos_count', 'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'inmutable', 'fecha_aprobacion', 'checksum',
            'created_at', 'updated_at',
        ]


class NodoEstrategicoSerializer(serializers.ModelSerializer):
    tipo_nodo_denominacion = serializers.CharField(
        source='tipo_nodo.denominacion', read_only=True,
    )
    padre_codigo = serializers.CharField(source='padre.codigo', read_only=True)

    class Meta:
        model = NodoEstrategico
        fields = [
            'id', 'version', 'tipo_nodo', 'tipo_nodo_denominacion',
            'padre', 'padre_codigo', 'codigo', 'nombre', 'descripcion',
            'orden', 'atributos', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class TipoNodoEstrategicoSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoNodoEstrategico
        fields = '__all__'
        read_only_fields = ['id']


class TipoVinculoEstrategicoSerializer(serializers.ModelSerializer):
    origen_denominacion = serializers.CharField(
        source='origen_permitido.denominacion', read_only=True,
    )
    destino_denominacion = serializers.CharField(
        source='destino_permitido.denominacion', read_only=True,
    )

    class Meta:
        model = TipoVinculoEstrategico
        fields = '__all__'
        read_only_fields = ['id']


class VinculoEstrategicoSerializer(serializers.ModelSerializer):
    origen_codigo = serializers.CharField(source='origen.codigo', read_only=True)
    origen_nombre = serializers.CharField(source='origen.nombre', read_only=True)
    destino_codigo = serializers.CharField(
        source='destino.codigo', read_only=True,
    )
    destino_nombre = serializers.CharField(
        source='destino.nombre', read_only=True,
    )
    tipo_denominacion = serializers.CharField(
        source='tipo.denominacion', read_only=True,
    )

    class Meta:
        model = VinculoEstrategico
        fields = [
            'id', 'version', 'origen', 'origen_codigo', 'origen_nombre',
            'destino', 'destino_codigo', 'destino_nombre', 'tipo',
            'tipo_denominacion', 'es_principal', 'ponderacion',
            'justificacion', 'validador', 'fecha_validacion', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']
