from rest_framework import serializers
from .models import (
    ClasificadorInstitucional, RubroRecurso, ObjetoGasto,
    FuenteFinanciamiento, OrganismoFinanciador, EntidadTransferencia,
    FinalidadFuncion, UnidadMedida, TipoOperacion, TipoProducto,
    TipoProyecto, TipoFinanciamiento, VersionCatalogo
)


class ClasificadorInstitucionalSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClasificadorInstitucional
        fields = '__all__'


class RubroRecursoSerializer(serializers.ModelSerializer):
    class Meta:
        model = RubroRecurso
        fields = '__all__'


class ObjetoGastoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ObjetoGasto
        fields = '__all__'


class FuenteFinanciamientoSerializer(serializers.ModelSerializer):
    class Meta:
        model = FuenteFinanciamiento
        fields = '__all__'


class OrganismoFinanciadorSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrganismoFinanciador
        fields = '__all__'


class EntidadTransferenciaSerializer(serializers.ModelSerializer):
    class Meta:
        model = EntidadTransferencia
        fields = '__all__'


class FinalidadFuncionSerializer(serializers.ModelSerializer):
    class Meta:
        model = FinalidadFuncion
        fields = '__all__'


class UnidadMedidaSerializer(serializers.ModelSerializer):
    class Meta:
        model = UnidadMedida
        fields = '__all__'


class TipoOperacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoOperacion
        fields = '__all__'


class TipoProductoSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoProducto
        fields = '__all__'


class TipoProyectoSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoProyecto
        fields = '__all__'


class TipoFinanciamientoSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoFinanciamiento
        fields = '__all__'


class VersionCatalogoSerializer(serializers.ModelSerializer):
    class Meta:
        model = VersionCatalogo
        fields = '__all__'
