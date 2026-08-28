from rest_framework import serializers
from .models import (
    DirigenteTerritorial, Distrito, LocalizacionTerritorial, UnidadTerritorial,
)


class DistritoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Distrito
        fields = '__all__'


class UnidadTerritorialSerializer(serializers.ModelSerializer):
    class Meta:
        model = UnidadTerritorial
        fields = '__all__'


class DirigenteTerritorialSerializer(serializers.ModelSerializer):
    unidad_nombre = serializers.CharField(source='unidad.nombre', read_only=True)

    class Meta:
        model = DirigenteTerritorial
        fields = ['id', 'unidad', 'unidad_nombre', 'gestion', 'nombre', 'cargo',
                  'telefono', 'vigente', 'observacion']


class OrganizacionDominioSerializer(serializers.ModelSerializer):
    """Lo mínimo para llenar los campos del acta.

    Deja afuera geometrías y superficies a propósito: esto alimenta un
    desplegable, no un mapa.
    """
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    distrito_codigo = serializers.CharField(source='distrito.codigo', read_only=True)
    dirigente = serializers.SerializerMethodField()
    cargo = serializers.SerializerMethodField()
    telefono = serializers.SerializerMethodField()

    class Meta:
        model = UnidadTerritorial
        fields = ['id', 'codigo', 'nombre', 'tipo', 'tipo_display', 'distrito',
                  'distrito_codigo', 'dirigente', 'cargo', 'telefono']

    def _dirigente(self, obj):
        # `dirigentes_vigentes` lo precarga la vista; sin eso serían N consultas.
        precargados = getattr(obj, 'dirigentes_vigentes', None)
        if precargados is not None:
            return precargados[0] if precargados else None
        return obj.dirigente_vigente

    def get_dirigente(self, obj):
        dirigente = self._dirigente(obj)
        return dirigente.nombre if dirigente else ''

    def get_cargo(self, obj):
        dirigente = self._dirigente(obj)
        return dirigente.cargo if dirigente else ''

    def get_telefono(self, obj):
        dirigente = self._dirigente(obj)
        return dirigente.telefono if dirigente else ''


class LocalizacionTerritorialSerializer(serializers.ModelSerializer):
    class Meta:
        model = LocalizacionTerritorial
        fields = '__all__'
