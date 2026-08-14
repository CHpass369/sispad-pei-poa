"""Serializers de la API V2 del ciclo presupuestario SIS-POA.

Fase 1: gestiÃ³n fiscal (FiscalYearSerializer).
Fase 2: techo directivo (DirectiveCeiling, versiones, recursos, gastos
obligatorios y documentos).

Los montos (DecimalField) se serializan como string por convenciÃ³n de DRF
(COERCE_DECIMAL_TO_STRING) y se respeta en la composiciÃ³n (str(Decimal)).
"""
from decimal import Decimal

from django.db import IntegrityError
from rest_framework import serializers

from apps.gestion.models import GestionFiscal

from .models import (
    BudgetDocument,
    CeilingResource,
    DirectiveCeiling,
    DirectiveCeilingVersion,
    EstadosTecho,
    MandatoryExpense,
)
from .services import (
    composicion_techo,
    crear_version_inicial,
    heredar_configuracion,
    validar_gestion_para_techo,
)


class FiscalYearSerializer(serializers.ModelSerializer):
    """GestiÃ³n fiscal del ciclo presupuestario (`apps.gestion.GestionFiscal`)."""

    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    gestion_anterior = serializers.SerializerMethodField()
    heredar_de = serializers.IntegerField(
        write_only=True, required=False, allow_null=True,
        help_text='AÃ±o de la gestiÃ³n de la cual heredar la configuraciÃ³n '
                  '(ciclos de formulaciÃ³n). Solo al crear.',
    )

    class Meta:
        model = GestionFiscal
        fields = [
            'id', 'anio', 'estado', 'estado_display', 'descripcion',
            'anio_inicio_plurianual', 'anio_fin_plurianual',
            'fecha_apertura', 'fecha_cierre', 'activa',
            'gestion_anterior', 'heredar_de', 'creado_en', 'actualizado_en',
        ]
        read_only_fields = [
            'id', 'estado', 'estado_display', 'fecha_apertura',
            'fecha_cierre', 'gestion_anterior', 'creado_en', 'actualizado_en',
        ]

    def get_gestion_anterior(self, obj):
        anterior = (
            GestionFiscal.objects.filter(anio__lt=obj.anio)
            .order_by('-anio').first()
        )
        return anterior.anio if anterior else None

    def create(self, validated_data):
        heredar_de = validated_data.pop('heredar_de', None)
        origen = None
        if heredar_de is not None:
            origen = GestionFiscal.objects.filter(anio=heredar_de).first()
            if origen is None:
                raise serializers.ValidationError({
                    'heredar_de': f'No existe una gestiÃ³n para el aÃ±o {heredar_de}.',
                })

        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['creado_por'] = request.user

        gestion = GestionFiscal(**validated_data)
        try:
            gestion.save()
        except IntegrityError:
            raise serializers.ValidationError({
                'anio': f'Ya existe una gestiÃ³n para el aÃ±o {validated_data["anio"]}.',
            })

        if origen is not None:
            heredar_configuracion(gestion, origen)
        return gestion


# ---------------------------------------------------------------------------
# Fase 2 â€” Techo directivo
# ---------------------------------------------------------------------------

def _detalle_catalogo(objeto):
    """{'codigo', 'denominacion'} del catÃ¡logo o None."""
    if objeto is None:
        return None
    return {'codigo': objeto.codigo, 'denominacion': objeto.denominacion}


def _detalle_unidad(objeto):
    """{'codigo', 'nombre'} de DA/UE o None."""
    if objeto is None:
        return None
    return {'codigo': objeto.codigo, 'nombre': objeto.nombre}


def _serializar_montos(valor):
    """Decimal â†’ str (convenciÃ³n COERCE_DECIMAL_TO_STRING de DRF) recursivo."""
    if isinstance(valor, Decimal):
        return str(valor)
    if isinstance(valor, dict):
        return {k: _serializar_montos(v) for k, v in valor.items()}
    if isinstance(valor, (list, tuple)):
        return [_serializar_montos(v) for v in valor]
    return valor


class CeilingResourceSerializer(serializers.ModelSerializer):
    origen_display = serializers.CharField(source='get_origen_display', read_only=True)
    rubro_detalle = serializers.SerializerMethodField()
    fuente_detalle = serializers.SerializerMethodField()
    organismo_detalle = serializers.SerializerMethodField()
    entidad_detalle = serializers.SerializerMethodField()
    documento_nombre = serializers.CharField(
        source='documento.nombre', read_only=True, default=None,
    )

    class Meta:
        model = CeilingResource
        fields = [
            'id', 'version', 'origen', 'origen_display', 'rubro', 'rubro_detalle',
            'fuente', 'fuente_detalle', 'organismo', 'organismo_detalle',
            'entidad_otorgante', 'entidad_detalle', 'concepto', 'monto',
            'documento', 'documento_nombre', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_rubro_detalle(self, obj) -> dict | None:
        return _detalle_catalogo(obj.rubro)

    def get_fuente_detalle(self, obj) -> dict | None:
        return _detalle_catalogo(obj.fuente)

    def get_organismo_detalle(self, obj) -> dict | None:
        return _detalle_catalogo(obj.organismo)

    def get_entidad_detalle(self, obj) -> dict | None:
        return _detalle_catalogo(obj.entidad_otorgante)


class MandatoryExpenseSerializer(serializers.ModelSerializer):
    da_detalle = serializers.SerializerMethodField()
    ue_detalle = serializers.SerializerMethodField()
    fuente_detalle = serializers.SerializerMethodField()
    organismo_detalle = serializers.SerializerMethodField()
    objeto_gasto_detalle = serializers.SerializerMethodField()
    documento_nombre = serializers.CharField(
        source='documento.nombre', read_only=True, default=None,
    )

    class Meta:
        model = MandatoryExpense
        fields = [
            'id', 'version', 'da', 'da_detalle', 'ue', 'ue_detalle',
            'programa', 'actividad', 'denominacion', 'fuente', 'fuente_detalle',
            'organismo', 'organismo_detalle', 'objeto_gasto', 'objeto_gasto_detalle',
            'entidad_transferencia', 'monto', 'documento', 'documento_nombre',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_da_detalle(self, obj) -> dict | None:
        return _detalle_unidad(obj.da)

    def get_ue_detalle(self, obj) -> dict | None:
        return _detalle_unidad(obj.ue)

    def get_fuente_detalle(self, obj) -> dict | None:
        return _detalle_catalogo(obj.fuente)

    def get_organismo_detalle(self, obj) -> dict | None:
        return _detalle_catalogo(obj.organismo)

    def get_objeto_gasto_detalle(self, obj) -> dict | None:
        return _detalle_catalogo(obj.objeto_gasto)


class DirectiveCeilingVersionSerializer(serializers.ModelSerializer):
    """VersiÃ³n del techo con sus recursos y gastos obligatorios anidados."""

    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    fijado_por_email = serializers.SerializerMethodField()
    recursos = CeilingResourceSerializer(many=True, read_only=True)
    gastos_obligatorios = MandatoryExpenseSerializer(many=True, read_only=True)

    class Meta:
        model = DirectiveCeilingVersion
        fields = [
            'id', 'numero', 'estado', 'estado_display', 'hash',
            'fecha_fijacion', 'fijado_por', 'fijado_por_email',
            'observaciones', 'inmutable', 'recursos', 'gastos_obligatorios',
            'created_at', 'updated_at',
        ]
        read_only_fields = fields

    def get_fijado_por_email(self, obj) -> str | None:
        return obj.fijado_por.email if obj.fijado_por else None


class DirectiveCeilingSerializer(serializers.ModelSerializer):
    """Techo directivo: gestiÃ³n, estado, versiÃ³n actual y composiciÃ³n anidada."""

    gestion_anio = serializers.IntegerField(source='gestion.anio', read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    version = serializers.SerializerMethodField()
    composicion = serializers.SerializerMethodField()

    class Meta:
        model = DirectiveCeiling
        fields = [
            'id', 'gestion', 'gestion_anio', 'estado', 'estado_display',
            'version_actual', 'version', 'composicion',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'estado', 'estado_display', 'version_actual',
            'created_at', 'updated_at',
        ]

    def _version(self, obj) -> DirectiveCeilingVersion | None:
        if obj.version_actual is None:
            return None
        return (
            DirectiveCeilingVersion.objects
            .filter(ceiling=obj, numero=obj.version_actual)
            .select_related('fijado_por')
            .prefetch_related(
                'recursos',
                'gastos_obligatorios',
            )
            .first()
        )

    def get_version(self, obj) -> dict | None:
        version = self._version(obj)
        return DirectiveCeilingVersionSerializer(
            version, context=self.context
        ).data if version else None

    def get_composicion(self, obj) -> dict:
        return _serializar_montos(composicion_techo(obj))

    def create(self, validated_data):
        gestion = validated_data['gestion']
        try:
            validar_gestion_para_techo(gestion)
        except Exception as exc:
            raise serializers.ValidationError({'gestion': exc.messages})

        if DirectiveCeiling.objects.filter(gestion=gestion).exists():
            raise serializers.ValidationError({
                'gestion': f'Ya existe un techo directivo para la gestiÃ³n {gestion.anio}.',
            })

        request = self.context.get('request')
        usuario = request.user if request and request.user.is_authenticated else None
        ceiling = DirectiveCeiling.objects.create(
            gestion=gestion,
            estado=EstadosTecho.BORRADOR,
            version_actual=1,
            created_by=usuario,
            updated_by=usuario,
        )
        crear_version_inicial(ceiling, usuario)
        return ceiling


class BudgetDocumentSerializer(serializers.ModelSerializer):
    """Documento de respaldo del techo; el upload valida mime y tamaÃ±o."""

    TAMANO_MAXIMO_BYTES = 20 * 1024 * 1024  # 20 MB
    MIMES_PERMITIDOS = {
        'application/pdf',
        'image/png',
        'image/jpeg',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'application/vnd.ms-excel',
        'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'text/csv',
        'application/csv',
        'text/plain',
    }
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    gestion_anio = serializers.IntegerField(source='gestion.anio', read_only=True)
    storage_path = serializers.SerializerMethodField()
    archivo = serializers.FileField(write_only=True, allow_empty_file=False)

    class Meta:
        model = BudgetDocument
        fields = [
            'id', 'gestion', 'gestion_anio', 'tipo', 'tipo_display',
            'nombre', 'mime_type', 'size', 'sha256', 'fecha_documento',
            'storage_path', 'metadata_json', 'archivo',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'mime_type', 'size', 'sha256', 'storage_path',
            'created_at', 'updated_at',
        ]
        extra_kwargs = {
            'nombre': {
                'required': False,
                'help_text': 'Opcional: por defecto usa el nombre del archivo.',
            },
            'metadata_json': {'required': False},
        }

    def get_storage_path(self, obj) -> str:
        return obj.storage_path

    def validate_archivo(self, archivo):
        if archivo.size > self.TAMANO_MAXIMO_BYTES:
            raise serializers.ValidationError(
                'El archivo supera el tamaÃ±o mÃ¡ximo de 20 MB.'
            )
        mime = getattr(archivo, 'content_type', '') or ''
        if mime not in self.MIMES_PERMITIDOS:
            raise serializers.ValidationError(
                f'Tipo de archivo no permitido ({mime or "desconocido"}). '
                'Permitidos: PDF, imÃ¡genes, Excel, Word, CSV y texto.'
            )
        return archivo

    def create(self, validated_data):
        archivo = validated_data.pop('archivo')
        nombre = validated_data.pop('nombre', '') or archivo.name
        request = self.context.get('request')
        usuario = request.user if request and request.user.is_authenticated else None
        documento = BudgetDocument.objects.create(
            **validated_data,
            nombre=nombre,
            archivo=archivo,
            mime_type=archivo.content_type or '',
            created_by=usuario,
            updated_by=usuario,
        )
        return documento
