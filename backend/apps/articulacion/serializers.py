from rest_framework import serializers

from .programacion_mensual import (
    EjecucionMensualMixin, ProgramacionMensualMixin,
)
from .models import (
    CodigoNivel, AcuerdoInternacional, CompatibilidadAcuerdoInternacional,
    Normativa, LineamientoPAD,
    ResultadoPAD, ProductoPAD, ResultadoPEI, ProductoPEI, BorradorMatrizPEI,
    ArticulacionPADPEI, IndicadorCadena, AccionPOA, OperacionPOAU,
    ActividadPOAU, ActividadNormativa, TareaPOAU, TareaNormativa,
    SeguimientoPresupuesto, AsignacionObjetoGasto, BorradorMatrizPAD,
    BorradorMatrizPOA,
)


# T2/T3 boundary: these values are observable through CRUD responses, but only
# the future CodificadorService may assign, normalize, or promote them.
CODIFICACION_READ_ONLY_FIELDS = [
    'correlativo',
    'segmento',
    'codigo_fuente',
    'codigo_normalizado',
    'codigo_completo_articulacion',
    'articulacion_incompleta',
    'estado_codigo',
]
AUDIT_READ_ONLY_FIELDS = [
    'id', 'created_at', 'updated_at', 'created_by', 'updated_by',
]


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


class CompatibilidadAcuerdoInternacionalSerializer(serializers.ModelSerializer):
    origen = AcuerdoInternacionalSerializer(read_only=True)
    destino = AcuerdoInternacionalSerializer(read_only=True)
    tipo_relacion_display = serializers.CharField(
        source='get_tipo_relacion_display', read_only=True,
    )
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    confianza_display = serializers.CharField(
        source='get_confianza_display', read_only=True,
    )

    class Meta:
        model = CompatibilidadAcuerdoInternacional
        fields = [
            'id', 'origen', 'destino', 'tipo_relacion', 'tipo_relacion_display',
            'estado', 'estado_display', 'confianza', 'confianza_display',
            'fuente_url', 'fuente_titulo', 'fuente_version', 'localizador',
            'evidencia', 'justificacion', 'activo', 'created_at', 'updated_at',
            'revisado_por', 'revisado_en',
        ]
        read_only_fields = fields


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
    nodo_pdesa_display = serializers.SerializerMethodField()

    class Meta:
        model = ResultadoPAD
        fields = '__all__'
        read_only_fields = AUDIT_READ_ONLY_FIELDS + CODIFICACION_READ_ONLY_FIELDS

    def get_nodo_pdesa_display(self, obj):
        if obj.nodo_pdesa:
            return f'[{obj.nodo_pdesa.codigo}] {obj.nodo_pdesa.nombre[:80]}'
        return None


class ProductoPADSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductoPAD
        fields = '__all__'
        read_only_fields = AUDIT_READ_ONLY_FIELDS + CODIFICACION_READ_ONLY_FIELDS


class ResultadoPEISerializer(serializers.ModelSerializer):
    class Meta:
        model = ResultadoPEI
        fields = '__all__'
        read_only_fields = AUDIT_READ_ONLY_FIELDS + CODIFICACION_READ_ONLY_FIELDS


class ProductoPEISerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductoPEI
        fields = '__all__'
        read_only_fields = AUDIT_READ_ONLY_FIELDS + CODIFICACION_READ_ONLY_FIELDS


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
        read_only_fields = AUDIT_READ_ONLY_FIELDS + CODIFICACION_READ_ONLY_FIELDS


class OperacionPOAUSerializer(ProgramacionMensualMixin, serializers.ModelSerializer):
    class Meta:
        model = OperacionPOAU
        fields = '__all__'
        read_only_fields = AUDIT_READ_ONLY_FIELDS + CODIFICACION_READ_ONLY_FIELDS


class ActividadPOAUSerializer(ProgramacionMensualMixin, serializers.ModelSerializer):
    class Meta:
        model = ActividadPOAU
        fields = '__all__'
        read_only_fields = AUDIT_READ_ONLY_FIELDS + CODIFICACION_READ_ONLY_FIELDS


class ActividadNormativaSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActividadNormativa
        fields = '__all__'
        read_only_fields = ['id']


class TareaPOAUSerializer(ProgramacionMensualMixin, serializers.ModelSerializer):
    class Meta:
        model = TareaPOAU
        fields = '__all__'
        read_only_fields = AUDIT_READ_ONLY_FIELDS + CODIFICACION_READ_ONLY_FIELDS


class TareaNormativaSerializer(serializers.ModelSerializer):
    class Meta:
        model = TareaNormativa
        fields = '__all__'
        read_only_fields = ['id']


class SeguimientoPresupuestoSerializer(EjecucionMensualMixin, serializers.ModelSerializer):
    presupuesto_vigente_calculado = serializers.SerializerMethodField()

    class Meta:
        model = SeguimientoPresupuesto
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by', 'updated_by']

    def get_presupuesto_vigente_calculado(self, obj):
        return (obj.presupuesto_inicial or 0) + (obj.modificaciones or 0)


class AsignacionObjetoGastoSerializer(ProgramacionMensualMixin, serializers.ModelSerializer):
    monto_vigente_calculado = serializers.SerializerMethodField()

    class Meta:
        model = AsignacionObjetoGasto
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by', 'updated_by']

    def get_monto_vigente_calculado(self, obj):
        return (obj.monto_programado or 0) + (obj.monto_modificado or 0)


class BorradorMatrizPADSerializer(serializers.ModelSerializer):
    """Serializador del borrador incremental de Matrices PAD.

    El PATCH acepta dos contratos:
    - Por sección: ``{"seccion": "resultados", "valores": [...lista...]}``
      (guardado incremental por paso del wizard; la colección ``resultados``
      se envía completa: el wizard la mantiene en memoria y la reemplaza al
      agregar/editar resultado o producto).
    - Completo: ``{"datos": {...}}`` (reemplaza todo el JSON de secciones).

    Las secciones legacy p6..p10 (cadena única) se aceptan en el PATCH y se
    transforman a la colección en lectura (retrocompatibilidad).
    """


    # --- Circuito de revisión -------------------------------------------
    estado_revision_display = serializers.CharField(
        source='get_estado_revision_display', read_only=True,
    )
    validado_por_nombre = serializers.SerializerMethodField()
    aprobado_por_nombre = serializers.SerializerMethodField()
    observado_por_nombre = serializers.SerializerMethodField()
    permisos = serializers.SerializerMethodField()

    def _nombre(self, usuario):
        if not usuario:
            return ''
        return usuario.get_full_name() or usuario.get_username()

    def get_validado_por_nombre(self, obj):
        return self._nombre(obj.validado_por)

    def get_aprobado_por_nombre(self, obj):
        return self._nombre(obj.aprobado_por)

    def get_observado_por_nombre(self, obj):
        return self._nombre(obj.observado_por)

    def get_permisos(self, obj):
        """Qué puede hacer el usuario de la petición sobre este registro."""
        from .permissions import permisos_revision_matriz
        usuario = getattr(self.context.get('request'), 'user', None)
        return permisos_revision_matriz(obj, usuario)

    class Meta:
        model = BorradorMatrizPAD
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by', 'updated_by']


def validar_estructura_resultados(valores):
    """Valida la estructura de la colección ``resultados`` del PATCH.

    Retorna un mensaje de error (str) si la estructura es inválida; None si
    es válida. Cada resultado debe ser un dict con ``denominacion`` y una
    lista ``productos`` (cada producto un dict con ``denominacion``).
    """
    if not isinstance(valores, list):
        return 'La sección "resultados" debe ser una lista de resultados.'
    if not valores:
        return 'La sección "resultados" no puede estar vacía: agregue al menos un resultado.'
    for i, resultado in enumerate(valores):
        if not isinstance(resultado, dict):
            return f'El resultado {i + 1} debe ser un objeto (dict).'
        if not str(resultado.get('denominacion', '')).strip():
            return f'El resultado {i + 1} debe tener una denominación.'
        productos = resultado.get('productos')
        if not isinstance(productos, list):
            return (
                f'El resultado {i + 1} ("{resultado.get("denominacion", "")}") '
                'debe tener una lista "productos".'
            )
        for j, producto in enumerate(productos):
            if not isinstance(producto, dict):
                return f'El producto {j + 1} del resultado {i + 1} debe ser un objeto (dict).'
            if not str(producto.get('denominacion', '')).strip():
                return f'El producto {j + 1} del resultado {i + 1} debe tener una denominación.'
    return None


class BorradorMatrizPEISerializer(serializers.ModelSerializer):
    """Borrador del asistente de Matriz PEI, con su circuito de revisión."""

    estado_revision_display = serializers.CharField(
        source='get_estado_revision_display', read_only=True,
    )
    validado_por_nombre = serializers.SerializerMethodField()
    aprobado_por_nombre = serializers.SerializerMethodField()
    observado_por_nombre = serializers.SerializerMethodField()
    permisos = serializers.SerializerMethodField()

    class Meta:
        model = BorradorMatrizPEI
        fields = '__all__'
        read_only_fields = AUDIT_READ_ONLY_FIELDS + [
            'estado_revision', 'validado_por', 'validado_en',
            'aprobado_por', 'aprobado_en', 'observacion',
            'observado_por', 'observado_en', 'id_resultado_pei',
        ]

    def _nombre(self, usuario):
        if not usuario:
            return ''
        return usuario.get_full_name() or usuario.get_username()

    def get_validado_por_nombre(self, obj):
        return self._nombre(obj.validado_por)

    def get_aprobado_por_nombre(self, obj):
        return self._nombre(obj.aprobado_por)

    def get_observado_por_nombre(self, obj):
        return self._nombre(obj.observado_por)

    def get_permisos(self, obj):
        from .permissions import permisos_revision_matriz
        usuario = getattr(self.context.get('request'), 'user', None)
        return permisos_revision_matriz(obj, usuario)


class BorradorMatrizPOASerializer(serializers.ModelSerializer):
    """Borrador del asistente de Matriz POA, con su circuito de revisión."""

    estado_revision_display = serializers.CharField(
        source='get_estado_revision_display', read_only=True,
    )
    validado_por_nombre = serializers.SerializerMethodField()
    aprobado_por_nombre = serializers.SerializerMethodField()
    observado_por_nombre = serializers.SerializerMethodField()
    permisos = serializers.SerializerMethodField()

    class Meta:
        model = BorradorMatrizPOA
        fields = '__all__'
        read_only_fields = AUDIT_READ_ONLY_FIELDS + [
            'estado_revision', 'validado_por', 'validado_en',
            'aprobado_por', 'aprobado_en', 'observacion',
            'observado_por', 'observado_en', 'id_accion_poa',
        ]

    def _nombre(self, usuario):
        if not usuario:
            return ''
        return usuario.get_full_name() or usuario.get_username()

    def get_validado_por_nombre(self, obj):
        return self._nombre(obj.validado_por)

    def get_aprobado_por_nombre(self, obj):
        return self._nombre(obj.aprobado_por)

    def get_observado_por_nombre(self, obj):
        return self._nombre(obj.observado_por)

    def get_permisos(self, obj):
        from .permissions import permisos_revision_matriz
        usuario = getattr(self.context.get('request'), 'user', None)
        return permisos_revision_matriz(obj, usuario)
