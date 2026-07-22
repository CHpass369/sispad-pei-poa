from rest_framework import serializers
from .models import (
    CodigoNivel, AcuerdoInternacional, Normativa, LineamientoPAD,
    ResultadoPAD, ProductoPAD, ResultadoPEI, ProductoPEI,
    ArticulacionPADPEI, IndicadorCadena, AccionPOA, OperacionPOAU,
    ActividadPOAU, ActividadNormativa, TareaPOAU, TareaNormativa,
    SeguimientoPresupuesto, AsignacionObjetoGasto,
)


class CodigoNivelSerializer(serializers.ModelSerializer):
    class Meta:
        model = CodigoNivel
        fields = '__all__'
        read_only_fields = ['id']


class AcuerdoInternacionalSerializer(serializers.ModelSerializer):
    tipo_acuerdo_display = serializers.CharField(
        source='get_tipo_acuerdo_display', read_only=True
    )

    class Meta:
        model = AcuerdoInternacional
        fields = '__all__'
        read_only_fields = ['id']


class NormativaSerializer(serializers.ModelSerializer):
    nivel_display = serializers.CharField(source='get_nivel_display', read_only=True)

    class Meta:
        model = Normativa
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by', 'updated_by']


class LineamientoPADSerializer(serializers.ModelSerializer):
    class Meta:
        model = LineamientoPAD
        fields = '__all__'
        read_only_fields = ['id']


class ResultadoPADSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResultadoPAD
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by', 'updated_by']


class ProductoPADSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductoPAD
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by', 'updated_by']


class ResultadoPEISerializer(serializers.ModelSerializer):
    class Meta:
        model = ResultadoPEI
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by', 'updated_by']


class ProductoPEISerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductoPEI
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by', 'updated_by']


class ArticulacionPADPEISerializer(serializers.ModelSerializer):
    producto_pad_display = serializers.SerializerMethodField()
    producto_pei_display = serializers.SerializerMethodField()

    class Meta:
        model = ArticulacionPADPEI
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by', 'updated_by']

    def get_producto_pad_display(self, obj):
        return f'[{obj.producto_pad.codigo_producto}] {obj.producto_pad.denominacion[:80]}'

    def get_producto_pei_display(self, obj):
        return f'[{obj.producto_pei.codigo_producto}] {obj.producto_pei.denominacion[:80]}'


class IndicadorCadenaSerializer(serializers.ModelSerializer):
    class Meta:
        model = IndicadorCadena
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by', 'updated_by']


class AccionPOASerializer(serializers.ModelSerializer):
    class Meta:
        model = AccionPOA
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by', 'updated_by']


class OperacionPOAUSerializer(serializers.ModelSerializer):
    class Meta:
        model = OperacionPOAU
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by', 'updated_by']


class ActividadPOAUSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActividadPOAU
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by', 'updated_by']


class ActividadNormativaSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActividadNormativa
        fields = '__all__'
        read_only_fields = ['id']


class TareaPOAUSerializer(serializers.ModelSerializer):
    class Meta:
        model = TareaPOAU
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by', 'updated_by']


class TareaNormativaSerializer(serializers.ModelSerializer):
    class Meta:
        model = TareaNormativa
        fields = '__all__'
        read_only_fields = ['id']


class SeguimientoPresupuestoSerializer(serializers.ModelSerializer):
    presupuesto_vigente_calculado = serializers.SerializerMethodField()

    class Meta:
        model = SeguimientoPresupuesto
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by', 'updated_by']

    def get_presupuesto_vigente_calculado(self, obj):
        return (obj.presupuesto_inicial or 0) + (obj.modificaciones or 0)


class AsignacionObjetoGastoSerializer(serializers.ModelSerializer):
    monto_vigente_calculado = serializers.SerializerMethodField()

    class Meta:
        model = AsignacionObjetoGasto
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by', 'updated_by']

    def get_monto_vigente_calculado(self, obj):
        return (obj.monto_programado or 0) + (obj.monto_modificado or 0)
