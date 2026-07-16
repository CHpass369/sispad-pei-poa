from django.core.exceptions import ValidationError
from rest_framework import serializers
from .models import (
    SectorPAD, PoliticaPAD, LineamientoEstrategico,
    ResultadoTerritorial, ProductoTerritorial, ArticulacionSIPEB,
    ProgramacionAnualPAD,
)


class SectorPADSerializer(serializers.ModelSerializer):
    class Meta:
        model = SectorPAD
        fields = '__all__'


class PoliticaPADSerializer(serializers.ModelSerializer):
    class Meta:
        model = PoliticaPAD
        fields = '__all__'


class LineamientoEstrategicoSerializer(serializers.ModelSerializer):
    politica_nombre = serializers.CharField(
        source='politica.nombre', read_only=True
    )

    class Meta:
        model = LineamientoEstrategico
        fields = '__all__'


class ProgramacionAnualPADSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProgramacionAnualPAD
        fields = ['id', 'resultado', 'producto', 'anio', 'tipo', 'valor']
        extra_kwargs = {
            'resultado': {'required': False},
            'producto': {'required': False},
        }

    def validate_valor(self, value):
        if value < 0:
            raise serializers.ValidationError("El valor no puede ser negativo")
        return value

    def validate(self, data):
        # Validar FK solo en uso standalone (no nested desde resultado/producto)
        if not self.parent:
            if not data.get('resultado') and not data.get('producto'):
                raise serializers.ValidationError(
                    "Debe especificar al menos resultado o producto territorial"
                )
        return data

    def create(self, validated_data):
        try:
            return super().create(validated_data)
        except ValidationError as e:
            raise serializers.ValidationError(e.message_dict)

    def update(self, instance, validated_data):
        try:
            return super().update(instance, validated_data)
        except ValidationError as e:
            raise serializers.ValidationError(e.message_dict)


class ProductoTerritorialSerializer(serializers.ModelSerializer):
    programaciones = serializers.ListField(
        child=serializers.DictField(), required=False, write_only=True
    )
    # JSONFields deprecated — solo lectura
    programacion_fisica = serializers.JSONField(read_only=True)
    programacion_financiera = serializers.JSONField(read_only=True)

    class Meta:
        model = ProductoTerritorial
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']
        extra_kwargs = {
            'cuenta_con_financiamiento': {'required': False},
            'presupuesto_total_pad': {'required': False},
        }

    def _crear_programaciones(self, instance, prog_data, fk_field='producto'):
        """Crea programaciones para un producto con FK forzado."""
        for item in prog_data:
            # Filtrar campos FK que vienen como None del serializer
            item = {k: v for k, v in item.items()
                    if k not in ('id', 'resultado', 'producto')}
            kwargs = {fk_field: instance, **item}
            ProgramacionAnualPAD.objects.create(**kwargs)

    def create(self, validated_data):
        prog_data = validated_data.pop('programaciones', [])
        producto = super().create(validated_data)
        self._crear_programaciones(producto, prog_data)
        return producto

    def update(self, instance, validated_data):
        prog_data = validated_data.pop('programaciones', None)
        instance = super().update(instance, validated_data)
        if prog_data is not None:
            instance.programaciones.all().delete()
            self._crear_programaciones(instance, prog_data)
        return instance


class ArticulacionSIPEBSerializer(serializers.ModelSerializer):
    class Meta:
        model = ArticulacionSIPEB
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class ResultadoTerritorialSerializer(serializers.ModelSerializer):
    productos = ProductoTerritorialSerializer(many=True, read_only=True)
    articulacion_sipeb = ArticulacionSIPEBSerializer(read_only=True)
    programaciones = serializers.ListField(
        child=serializers.DictField(), required=False, write_only=True
    )
    # JSONFields deprecated — solo lectura
    programacion_fisica = serializers.JSONField(read_only=True)
    programacion_financiera = serializers.JSONField(read_only=True)

    class Meta:
        model = ResultadoTerritorial
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']

    def _crear_programaciones(self, instance, prog_data, fk_field='resultado'):
        """Crea programaciones para un resultado con FK forzado."""
        for item in prog_data:
            # Filtrar campos FK que vienen como None del serializer
            item = {k: v for k, v in item.items()
                    if k not in ('id', 'resultado', 'producto')}
            kwargs = {fk_field: instance, **item}
            ProgramacionAnualPAD.objects.create(**kwargs)

    def create(self, validated_data):
        prog_data = validated_data.pop('programaciones', [])
        resultado = super().create(validated_data)
        self._crear_programaciones(resultado, prog_data)
        return resultado

    def update(self, instance, validated_data):
        prog_data = validated_data.pop('programaciones', None)
        instance = super().update(instance, validated_data)
        if prog_data is not None:
            instance.programaciones.all().delete()
            self._crear_programaciones(instance, prog_data)
        return instance


class ResultadoTerritorialListSerializer(serializers.ModelSerializer):
    """Serializer liviano para listados, evita N+1 en productos y articulación"""
    lineamiento_nombre = serializers.CharField(
        source='lineamiento.nombre', read_only=True
    )
    sector_nombre = serializers.CharField(
        source='sector.nombre', read_only=True, allow_null=True
    )

    class Meta:
        model = ResultadoTerritorial
        fields = [
            'id', 'codigo', 'nombre', 'lineamiento_nombre',
            'sector_nombre', 'indicador', 'gestion',
        ]


class CadenaCompletaSerializer(serializers.Serializer):
    """Serializer para la cadena PGDESA → PDESA → PDS → PAD → PEI → POA"""
    resultado = ResultadoTerritorialSerializer()
    articulacion = ArticulacionSIPEBSerializer(source='articulacion_sipeb')
    productos = ProductoTerritorialSerializer(many=True, source='productos.all')
    # PEI y POA se agregan via @action cuando exista vinculación
    pei = serializers.ListField(child=serializers.DictField(), default=[])
    poa = serializers.ListField(child=serializers.DictField(), default=[])
