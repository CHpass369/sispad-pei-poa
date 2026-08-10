"""Serializers del dominio de preinversión SIS-PRO (SISPRE / RM 115)."""
from rest_framework import serializers

from .models_preinversion import (
    ActividadTDR,
    AlternativaProyecto,
    AprobacionPreinversion,
    ComponenteProyecto,
    CondicionITCP,
    DocumentoGenerado,
    DocumentoPreinversion,
    EDTP,
    EstudioTecnico,
    FuenteFinanciamientoEDTP,
    GrupoBeneficiario,
    IndicadorEvaluacionEDTP,
    ITCP,
    ItemCostoEDTP,
    ItemCronograma,
    ItemPresupuestoTDR,
    ObservacionPreinversion,
    PersonalTDR,
    PlanOperacionMantenimiento,
    ProductoTDR,
    RevisionPreinversion,
    SeccionEDTP,
    SolicitudReformulacion,
    TDR,
    VersionDocumentoPreinversion,
)


# ---------------------------------------------------------------------------
# ITCP
# ---------------------------------------------------------------------------
class CondicionITCPSerializer(serializers.ModelSerializer):
    class Meta:
        model = CondicionITCP
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate(self, attrs):
        if attrs.get('estado') == 'no_aplica' and not attrs.get('justificacion_no_aplica'):
            raise serializers.ValidationError(
                'Debe justificar por qué la condición no aplica'
            )
        return attrs


class ITCPSerializer(serializers.ModelSerializer):
    condiciones = CondicionITCPSerializer(many=True, read_only=True)

    class Meta:
        model = ITCP
        fields = '__all__'
        read_only_fields = ['id', 'version', 'created_at', 'updated_at']


# ---------------------------------------------------------------------------
# TDR
# ---------------------------------------------------------------------------
class TDRActividadSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActividadTDR
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class TDRProductoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductoTDR
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class TDRPersonalSerializer(serializers.ModelSerializer):
    subtotal = serializers.DecimalField(max_digits=18, decimal_places=2, read_only=True)

    class Meta:
        model = PersonalTDR
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class TDRItemPresupuestoSerializer(serializers.ModelSerializer):
    subtotal = serializers.DecimalField(max_digits=18, decimal_places=2, read_only=True)

    class Meta:
        model = ItemPresupuestoTDR
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class TDRSerializer(serializers.ModelSerializer):
    actividades = TDRActividadSerializer(many=True, read_only=True)
    productos = TDRProductoSerializer(many=True, read_only=True)
    personal = TDRPersonalSerializer(many=True, read_only=True)
    items_presupuesto = TDRItemPresupuestoSerializer(many=True, read_only=True)

    class Meta:
        model = TDR
        fields = '__all__'
        read_only_fields = ['id', 'version', 'created_at', 'updated_at']


# ---------------------------------------------------------------------------
# EDTP
# ---------------------------------------------------------------------------
class SeccionEDTPSerializer(serializers.ModelSerializer):
    class Meta:
        model = SeccionEDTP
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate(self, attrs):
        if attrs.get('aplicable') is False and not attrs.get('justificacion_no_aplica'):
            raise serializers.ValidationError(
                'Debe justificar la no aplicabilidad de la sección'
            )
        return attrs


class EstudioTecnicoSerializer(serializers.ModelSerializer):
    class Meta:
        model = EstudioTecnico
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class ItemCostoEDTPSerializer(serializers.ModelSerializer):
    subtotal = serializers.DecimalField(max_digits=24, decimal_places=4, read_only=True)

    class Meta:
        model = ItemCostoEDTP
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class FuenteFinanciamientoSerializer(serializers.ModelSerializer):
    class Meta:
        model = FuenteFinanciamientoEDTP
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class ItemCronogramaSerializer(serializers.ModelSerializer):
    class Meta:
        model = ItemCronograma
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class PlanOMSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlanOperacionMantenimiento
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class IndicadorEvaluacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = IndicadorEvaluacionEDTP
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class EDTPSerializer(serializers.ModelSerializer):
    secciones = SeccionEDTPSerializer(many=True, read_only=True)
    estudios_tecnicos = EstudioTecnicoSerializer(many=True, read_only=True)
    items_costo = ItemCostoEDTPSerializer(many=True, read_only=True)
    fuentes_financiamiento = FuenteFinanciamientoSerializer(many=True, read_only=True)
    indicadores_evaluacion = IndicadorEvaluacionSerializer(many=True, read_only=True)
    plan_om = PlanOMSerializer(read_only=True)

    class Meta:
        model = EDTP
        fields = '__all__'
        read_only_fields = ['id', 'version', 'created_at', 'updated_at']


# ---------------------------------------------------------------------------
# Proyecto / expediente
# ---------------------------------------------------------------------------
class ComponenteProyectoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ComponenteProyecto
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class GrupoBeneficiarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = GrupoBeneficiario
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class AlternativaProyectoSerializer(serializers.ModelSerializer):
    class Meta:
        model = AlternativaProyecto
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class SolicitudReformulacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = SolicitudReformulacion
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class VersionDocumentoSerializer(serializers.ModelSerializer):
    class Meta:
        model = VersionDocumentoPreinversion
        fields = '__all__'
        read_only_fields = ['id', 'sha256', 'created_at', 'updated_at']


class DocumentoPreinversionSerializer(serializers.ModelSerializer):
    versiones = VersionDocumentoSerializer(many=True, read_only=True)

    class Meta:
        model = DocumentoPreinversion
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class DocumentoGeneradoSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentoGenerado
        fields = '__all__'
        read_only_fields = ['id', 'estado', 'archivo_docx', 'archivo_pdf',
                            'mensaje_error', 'contexto', 'created_at', 'updated_at']


# ---------------------------------------------------------------------------
# Revisión / observación / aprobación
# ---------------------------------------------------------------------------
class RevisionSerializer(serializers.ModelSerializer):
    class Meta:
        model = RevisionPreinversion
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class ObservacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ObservacionPreinversion
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class AprobacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AprobacionPreinversion
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']
