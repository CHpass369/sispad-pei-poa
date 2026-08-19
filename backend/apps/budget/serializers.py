"""Serializers de la API V2 del ciclo presupuestario SIS-POA.

Fase 1: gestión fiscal (GestionFiscalPresupuestoSerializer).
Fase 2: techo directivo (TechoDirectivo, versiones, recursos, gastos
obligatorios y documentos).

Los montos (DecimalField) se serializan como string por convención de DRF
(COERCE_DECIMAL_TO_STRING) y se respeta en la composición (str(Decimal)).
"""
from datetime import date
from decimal import Decimal

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError, models
from rest_framework import serializers

from apps.auditoria.models import EventoAuditoria
from apps.gestion.models import GestionFiscal

from .models import (
    Apertura,
    AperturaFuente,
    DocumentoPresupuestario,
    Importacion,
    RecursoTecho,
    TechoDirectivo,
    TechoVersion,
    DistribucionVersion,
    EstadosTecho,
    AsignacionObjetoGastoTecho,
    ImportacionError,
    GastoObligatorio,
    CategoriaProgramaticaTecho,
    Reforma,
    ReformaMovimiento,
    Reserva,
    AsignacionTerritorial,
    DistribucionTerritorial,
    TipoMovimientoReform,
)
from .services import (
    composicion_techo,
    crear_version_inicial,
    heredar_configuracion,
    validar_gestion_para_techo,
)


class GestionFiscalPresupuestoSerializer(serializers.ModelSerializer):
    """Gestión fiscal del ciclo presupuestario (`apps.gestion.GestionFiscal`)."""

    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    fecha_cargado = serializers.DateTimeField(source='creado_en', read_only=True)
    encargado_cargado = serializers.EmailField(
        source='creado_por.email', read_only=True, allow_null=True,
    )
    gestion_anterior = serializers.SerializerMethodField()
    heredar_de = serializers.IntegerField(
        write_only=True, required=False, allow_null=True,
        help_text='Año de la gestión de la cual heredar la configuración '
                  '(ciclos de formulación). Solo al crear.',
    )

    class Meta:
        model = GestionFiscal
        fields = [
            'id', 'anio', 'estado', 'estado_display', 'descripcion',
            'anio_inicio_plurianual', 'anio_fin_plurianual',
            'fecha_apertura', 'fecha_cierre', 'fecha_inicio',
            'fecha_cierre_programada', 'documento_habilitacion', 'activa',
            'gestion_anterior', 'heredar_de', 'creado_en', 'actualizado_en',
            'fecha_cargado', 'encargado_cargado',
        ]
        read_only_fields = [
            'id', 'estado', 'estado_display', 'fecha_apertura',
            'fecha_cierre', 'gestion_anterior', 'creado_en', 'actualizado_en',
            'fecha_cargado', 'encargado_cargado',
        ]

    def to_representation(self, instance):
        """Keep the annual dates safe for rows created before these fields."""
        data = super().to_representation(instance)
        data['fecha_inicio'] = (
            instance.fecha_inicio or date(instance.anio, 1, 1)
        ).isoformat()
        data['fecha_cierre_programada'] = (
            instance.fecha_cierre_programada or date(instance.anio, 12, 31)
        ).isoformat()
        return data

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
                    'heredar_de': f'No existe una gestión para el año {heredar_de}.',
                })

        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['creado_por'] = request.user

        gestion = GestionFiscal(**validated_data)
        try:
            gestion.save()
        except IntegrityError:
            raise serializers.ValidationError({
                'anio': f'Ya existe una gestión para el año {validated_data["anio"]}.',
            })

        if origen is not None:
            heredar_configuracion(gestion, origen)
        return gestion


# ---------------------------------------------------------------------------
# Fase 2 â€” Techo directivo
# ---------------------------------------------------------------------------

def _detalle_catalogo(objeto):
    """{'codigo', 'denominacion'} del catálogo o None."""
    if objeto is None:
        return None
    return {'codigo': objeto.codigo, 'denominacion': objeto.denominacion}


def _detalle_unidad(objeto):
    """{'codigo', 'nombre'} de DA/UE o None."""
    if objeto is None:
        return None
    return {'codigo': objeto.codigo, 'nombre': objeto.nombre}


def _serializar_montos(valor):
    """Decimal → str (convención COERCE_DECIMAL_TO_STRING de DRF) recursivo."""
    if isinstance(valor, Decimal):
        return str(valor)
    if isinstance(valor, dict):
        return {k: _serializar_montos(v) for k, v in valor.items()}
    if isinstance(valor, (list, tuple)):
        return [_serializar_montos(v) for v in valor]
    return valor


class RecursoTechoSerializer(serializers.ModelSerializer):
    origen_display = serializers.CharField(source='get_origen_display', read_only=True)
    rubro_detalle = serializers.SerializerMethodField()
    fuente_detalle = serializers.SerializerMethodField()
    organismo_detalle = serializers.SerializerMethodField()
    entidad_detalle = serializers.SerializerMethodField()
    documento_nombre = serializers.CharField(
        source='documento.nombre', read_only=True, default=None,
    )

    class Meta:
        model = RecursoTecho
        fields = [
            'id', 'version', 'origen', 'origen_display', 'rubro', 'rubro_detalle',
            'fuente', 'fuente_detalle', 'organismo', 'organismo_detalle',
            'entidad_otorgante', 'entidad_detalle', 'concepto', 'monto',
            'padre', 'orden', 'monto_corriente', 'monto_inversion',
            'porcentaje_corriente', 'porcentaje_inversion',
            'documento', 'documento_nombre', 'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at',
            # Derivados: se calculan, nunca se envian.
            'porcentaje_corriente', 'porcentaje_inversion',
        ]

    def get_rubro_detalle(self, obj) -> dict | None:
        return _detalle_catalogo(obj.rubro)

    def get_fuente_detalle(self, obj) -> dict | None:
        return _detalle_catalogo(obj.fuente)

    def get_organismo_detalle(self, obj) -> dict | None:
        return _detalle_catalogo(obj.organismo)

    def get_entidad_detalle(self, obj) -> dict | None:
        return _detalle_catalogo(obj.entidad_otorgante)


class GastoObligatorioSerializer(serializers.ModelSerializer):
    da_detalle = serializers.SerializerMethodField()
    ue_detalle = serializers.SerializerMethodField()
    fuente_detalle = serializers.SerializerMethodField()
    organismo_detalle = serializers.SerializerMethodField()
    objeto_gasto_detalle = serializers.SerializerMethodField()
    documento_nombre = serializers.CharField(
        source='documento.nombre', read_only=True, default=None,
    )

    class Meta:
        model = GastoObligatorio
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


class TechoVersionSerializer(serializers.ModelSerializer):
    """Versión del techo con sus recursos y gastos obligatorios anidados."""

    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    fijado_por_email = serializers.SerializerMethodField()
    recursos = RecursoTechoSerializer(many=True, read_only=True)
    gastos_obligatorios = GastoObligatorioSerializer(many=True, read_only=True)

    class Meta:
        model = TechoVersion
        fields = [
            'id', 'numero', 'estado', 'estado_display', 'hash',
            'fecha_fijacion', 'fijado_por', 'fijado_por_email',
            'observaciones', 'inmutable', 'recursos', 'gastos_obligatorios',
            'created_at', 'updated_at',
        ]
        read_only_fields = fields

    def get_fijado_por_email(self, obj) -> str | None:
        return obj.fijado_por.email if obj.fijado_por else None


class TechoDirectivoSerializer(serializers.ModelSerializer):
    """Techo directivo: gestión, estado, versión actual y composición anidada."""

    gestion_anio = serializers.IntegerField(source='gestion.anio', read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    version = serializers.SerializerMethodField()
    composicion = serializers.SerializerMethodField()

    class Meta:
        model = TechoDirectivo
        fields = [
            'id', 'gestion', 'gestion_anio', 'estado', 'estado_display',
            'version_actual', 'version', 'composicion',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'estado', 'estado_display', 'version_actual',
            'created_at', 'updated_at',
        ]

    def _version(self, obj) -> TechoVersion | None:
        if obj.version_actual is None:
            return None
        return (
            TechoVersion.objects
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
        return TechoVersionSerializer(
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

        if TechoDirectivo.objects.filter(gestion=gestion).exists():
            raise serializers.ValidationError({
                'gestion': f'Ya existe un techo directivo para la gestión {gestion.anio}.',
            })

        request = self.context.get('request')
        usuario = request.user if request and request.user.is_authenticated else None
        ceiling = TechoDirectivo.objects.create(
            gestion=gestion,
            estado=EstadosTecho.BORRADOR,
            version_actual=1,
            created_by=usuario,
            updated_by=usuario,
        )
        crear_version_inicial(ceiling, usuario)
        return ceiling


class DocumentoPresupuestarioSerializer(serializers.ModelSerializer):
    """Documento de respaldo del techo; el upload valida mime y tamaño."""

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
        model = DocumentoPresupuestario
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
                'El archivo supera el tamaño máximo de 20 MB.'
            )
        mime = getattr(archivo, 'content_type', '') or ''
        if mime not in self.MIMES_PERMITIDOS:
            raise serializers.ValidationError(
                f'Tipo de archivo no permitido ({mime or "desconocido"}). '
                'Permitidos: PDF, imágenes, Excel, Word, CSV y texto.'
            )
        return archivo

    def create(self, validated_data):
        archivo = validated_data.pop('archivo')
        nombre = validated_data.pop('nombre', '') or archivo.name
        request = self.context.get('request')
        usuario = request.user if request and request.user.is_authenticated else None
        documento = DocumentoPresupuestario.objects.create(
            **validated_data,
            nombre=nombre,
            archivo=archivo,
            mime_type=archivo.content_type or '',
            created_by=usuario,
            updated_by=usuario,
        )
        return documento


# ---------------------------------------------------------------------------
# Fase 3 - CategorAas programAticas del ciclo
# ---------------------------------------------------------------------------
class CategoriaProgramaticaTechoSerializer(serializers.ModelSerializer):
    nivel_display = serializers.CharField(source='get_nivel_display', read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    codigo_compuesto = serializers.SerializerMethodField()

    class Meta:
        model = CategoriaProgramaticaTecho
        fields = [
            'id', 'gestion', 'codigo', 'denominacion', 'nivel', 'nivel_display',
            'parent', 'vigencia_desde', 'vigencia_hasta', 'estado',
            'estado_display', 'origen', 'normativa', 'observaciones',
            'codigo_compuesto', 'created_at', 'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']

    def get_codigo_compuesto(self, obj):
        """Codigo jerAarquico: prog[.sub[.proy[.act]]] preservando ceros."""
        partes = []
        nodo = obj
        while nodo:
            partes.append(nodo.codigo)
            nodo = nodo.parent
        return '.'.join(reversed(partes))

    def _manejar_clean(self, fn, *args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except DjangoValidationError as e:
            raise serializers.ValidationError(e.message_dict) from e

    def create(self, validated_data):
        return self._manejar_clean(super().create, validated_data)

    def update(self, instance, validated_data):
        return self._manejar_clean(super().update, instance, validated_data)


# ---------------------------------------------------------------------------
# Fase 4 - Distribución presupuestaria (versiones, aperturas y reservas)
# ---------------------------------------------------------------------------
class DistribucionVersionSerializer(serializers.ModelSerializer):
    """Versión de distribución; estados reutilizan `EstadosTecho`."""

    gestion_anio = serializers.IntegerField(source='gestion.anio', read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    fijado_por_email = serializers.SerializerMethodField()

    class Meta:
        model = DistribucionVersion
        fields = [
            'id', 'gestion', 'gestion_anio', 'numero', 'estado',
            'estado_display', 'hash', 'fecha_fijacion', 'fijado_por',
            'fijado_por_email', 'observaciones', 'inmutable',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'estado', 'estado_display', 'hash', 'fecha_fijacion',
            'fijado_por', 'inmutable', 'created_at', 'updated_at',
        ]

    def get_fijado_por_email(self, obj) -> str | None:
        return obj.fijado_por.email if obj.fijado_por else None

    def validate(self, attrs):
        gestion = attrs.get('gestion')
        numero = attrs.get('numero')
        if gestion is not None and numero is not None:
            if DistribucionVersion.objects.filter(
                gestion=gestion, numero=numero,
            ).exists():
                raise serializers.ValidationError({
                    'numero': f'La versión {numero} ya existe para la gestión.',
                })
        return attrs


class AperturaFuenteSerializer(serializers.ModelSerializer):
    """Asignación por FF/OF (lectura, anidada en la apertura)."""

    fuente_detalle = serializers.SerializerMethodField()
    organismo_detalle = serializers.SerializerMethodField()

    class Meta:
        model = AperturaFuente
        fields = [
            'id', 'fuente', 'fuente_detalle', 'organismo',
            'organismo_detalle', 'monto', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_fuente_detalle(self, obj) -> dict | None:
        return _detalle_catalogo(obj.fuente)

    def get_organismo_detalle(self, obj) -> dict | None:
        return _detalle_catalogo(obj.organismo)


class AllocationFuenteInput(serializers.Serializer):
    """Fila de fuente del payload de create/update de una apertura."""

    fuente = serializers.UUIDField()
    organismo = serializers.UUIDField(required=False, allow_null=True, default=None)
    monto = serializers.DecimalField(
        max_digits=18, decimal_places=2, min_value=Decimal('0.01'),
    )


class AperturaSerializer(serializers.ModelSerializer):
    """Apertura programática con sus fuentes anidadas.

    Escritura: `fuentes` acepta [{fuente, organismo, monto}]; el viewset
    delega la creación/actualización al servicio (validación de
    disponibilidad y transacción). El estado lo gestionan los servicios.
    """

    fuentes = AperturaFuenteSerializer(many=True, read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    estado_revision_display = serializers.CharField(
        source='get_estado_revision_display', read_only=True)
    tipo_apertura_display = serializers.CharField(
        source='get_tipo_apertura_display', read_only=True,
    )
    gestion_anio = serializers.IntegerField(source='gestion.anio', read_only=True)
    total = serializers.SerializerMethodField()
    categoria_detalle = serializers.SerializerMethodField()
    da_detalle = serializers.SerializerMethodField()
    ue_detalle = serializers.SerializerMethodField()
    distrito_detalle = serializers.SerializerMethodField()
    unidad_detalle = serializers.SerializerMethodField()

    class Meta:
        model = Apertura
        fields = [
            'id', 'gestion', 'gestion_anio', 'version', 'orden',
            'unidad_organizacional', 'unidad_detalle', 'distrito',
            'distrito_detalle', 'da', 'da_detalle', 'ue', 'ue_detalle',
            'categoria', 'categoria_detalle', 'proyecto_codigo',
            'codigo_sisin', 'actividad_codigo', 'denominacion',
            'tipo_apertura', 'tipo_apertura_display', 'estado',
            'estado_display', 'estado_revision', 'estado_revision_display',
            'observacion', 'validado_en', 'aprobado_en',
            'fuentes', 'total', 'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'version', 'estado', 'estado_display', 'created_at',
            'updated_at',
        ]

    def get_total(self, obj) -> str:
        return str(obj.total)

    def get_categoria_detalle(self, obj) -> dict | None:
        c = obj.categoria
        if c is None:
            return None
        partes = []
        nodo = c
        while nodo:
            partes.append(nodo.codigo)
            nodo = nodo.parent
        return {
            'id': str(c.id),
            'codigo': c.codigo,
            'codigo_compuesto': '.'.join(reversed(partes)),
            'denominacion': c.denominacion,
        }

    def get_da_detalle(self, obj) -> dict | None:
        return _detalle_unidad(obj.da)

    def get_ue_detalle(self, obj) -> dict | None:
        return _detalle_unidad(obj.ue)

    def get_distrito_detalle(self, obj) -> dict | None:
        d = obj.distrito
        if d is None:
            return None
        return {'codigo': d.codigo, 'nombre': d.nombre}

    def get_unidad_detalle(self, obj) -> dict | None:
        u = obj.unidad_organizacional
        if u is None:
            return None
        return {'codigo': u.codigo, 'nombre': u.nombre}

    def to_internal_value(self, data):
        data = dict(data)
        fuentes_raw = data.pop('fuentes', None)
        validated = super().to_internal_value(data)
        if fuentes_raw is not None:
            if not isinstance(fuentes_raw, (list, tuple)):
                raise serializers.ValidationError({
                    'fuentes': 'Debe ser una lista de {fuente, organismo, monto}.',
                })
            entradas = []
            for i, fila in enumerate(fuentes_raw):
                serializador = AllocationFuenteInput(data=fila)
                if not serializador.is_valid():
                    raise serializers.ValidationError({
                        'fuentes': {i: serializador.errors},
                    })
                entradas.append(serializador.validated_data)
            validated['fuentes'] = entradas
        return validated


# ---------------------------------------------------------------------------
# Fase 9 - Objetos del gasto (programación por apertura)
# ---------------------------------------------------------------------------
class AsignacionObjetoGastoTechoSerializer(serializers.ModelSerializer):
    """Programación de un objeto del gasto en una apertura (Fase 9).

    Escritura: `allocation` + `objeto_gasto` + `monto`; el viewset delega
    en `services.programar_objeto_gasto` (upsert, control de disponibilidad
    contra el techo de la apertura y BUDGET_EXCEEDED → 409).
    """

    objeto_gasto_detalle = serializers.SerializerMethodField()

    class Meta:
        model = AsignacionObjetoGastoTecho
        fields = [
            'id', 'allocation', 'objeto_gasto', 'objeto_gasto_detalle',
            'monto', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_unique_together_validators(self):
        """La unicidad (allocation, objeto_gasto) la gestiona el servicio:
        `programar_objeto_gasto` es un UPSERT (crear con fila existente
        actualiza en lugar de rechazar). La constraint sigue en la BD."""
        return []

    def get_objeto_gasto_detalle(self, obj) -> dict | None:
        return _detalle_catalogo(obj.objeto_gasto)


class ReservaSerializer(serializers.ModelSerializer):
    """Reserva presupuestaria sobre una fuente."""

    gestion_anio = serializers.IntegerField(source='gestion.anio', read_only=True)
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    fuente_detalle = serializers.SerializerMethodField()
    organismo_detalle = serializers.SerializerMethodField()

    class Meta:
        model = Reserva
        fields = [
            'id', 'gestion', 'gestion_anio', 'version', 'fuente',
            'fuente_detalle', 'organismo', 'organismo_detalle', 'tipo',
            'tipo_display', 'monto', 'motivo', 'estado', 'estado_display',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'version', 'estado', 'estado_display', 'created_at',
            'updated_at',
        ]

    def get_fuente_detalle(self, obj) -> dict | None:
        return _detalle_catalogo(obj.fuente)

    def get_organismo_detalle(self, obj) -> dict | None:
        return _detalle_catalogo(obj.organismo)


# ---------------------------------------------------------------------------
# Fase 5 - Importador Excel (staging)
# ---------------------------------------------------------------------------
class ImportacionSerializer(serializers.ModelSerializer):
    """Importación de planilla; el upload valida mime/tamaño y parsea."""

    TAMANO_MAXIMO_BYTES = 20 * 1024 * 1024  # 20 MB
    MIMES_PERMITIDOS = {
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'application/vnd.ms-excel',
        'text/csv',
        'application/csv',
        'application/octet-stream',
    }
    gestion_anio = serializers.IntegerField(source='gestion.anio', read_only=True)
    perfil_display = serializers.CharField(
        source='get_perfil_display', read_only=True,
    )
    estado_display = serializers.CharField(
        source='get_estado_display', read_only=True,
    )
    archivo = serializers.FileField(write_only=True, allow_empty_file=False)
    conteos = serializers.SerializerMethodField()

    class Meta:
        model = Importacion
        fields = [
            'id', 'gestion', 'gestion_anio', 'perfil', 'perfil_display',
            'filename', 'mime_type', 'size', 'sha256', 'hoja_seleccionada',
            'mapeo_json', 'estado', 'estado_display', 'tipo_importacion',
            'storage_path', 'conteos', 'archivo', 'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'filename', 'mime_type', 'size', 'sha256',
            'hoja_seleccionada', 'mapeo_json', 'estado', 'estado_display',
            'storage_path', 'conteos', 'created_at', 'updated_at',
        ]

    def get_conteos(self, obj) -> dict:
        from django.db.models import Count
        conteos = {s: 0 for s, _ in _SEVERIDADES}
        for fila in obj.errores.values('severidad').annotate(n=Count('id')):
            conteos[fila['severidad']] = fila['n']
        return conteos

    def validate_archivo(self, archivo):
        if archivo.size > self.TAMANO_MAXIMO_BYTES:
            raise serializers.ValidationError(
                'El archivo supera el tamaño máximo de 20 MB.'
            )
        mime = getattr(archivo, 'content_type', '') or ''
        if mime not in self.MIMES_PERMITIDOS:
            raise serializers.ValidationError(
                f'Tipo de archivo no permitido ({mime or "desconocido"}). '
                'Permitidos: Excel (.xlsx/.xls) y CSV.'
            )
        return archivo

    def create(self, validated_data):
        archivo = validated_data.pop('archivo')
        request = self.context.get('request')
        usuario = request.user if request and request.user.is_authenticated else None
        importacion = Importacion.objects.create(
            **validated_data,
            filename=archivo.name,
            archivo=archivo,
            mime_type=archivo.content_type or '',
            creado_por=usuario,
            created_by=usuario,
            updated_by=usuario,
        )
        return importacion


_SEVERIDADES = (
    ('INFO', 'Info'),
    ('WARNING', 'Advertencia'),
    ('ERROR', 'Error'),
    ('CRITICAL', 'Crítico'),
)


class ImportErrorSerializer(serializers.ModelSerializer):
    """Error/hallazgo de la validación de una importación."""

    severidad_display = serializers.CharField(
        source='get_severidad_display', read_only=True,
    )
    accion_display = serializers.CharField(
        source='get_accion_display', read_only=True,
    )

    class Meta:
        model = ImportacionError
        fields = [
            'id', 'detalle', 'fila', 'campo', 'valor_original',
            'valor_normalizado', 'severidad', 'severidad_display',
            'mensaje', 'accion', 'accion_display', 'resuelto',
            'created_at', 'updated_at',
        ]
        read_only_fields = fields


# ---------------------------------------------------------------------------
# Fase 6 - Distribución territorial (reparto por distrito + reservas)
# ---------------------------------------------------------------------------
class TerritorialAllocationInput(serializers.Serializer):
    """Fila de distrito del payload de create/calcular (write-only).

    `poblacion` alimenta el método POBLACION, `porcentaje` el método
    PORCENTAJE (escala 0-100) y `monto` los métodos MANUAL/MONTO_FIJO/FORMULA.
    """

    distrito = serializers.UUIDField()
    poblacion = serializers.IntegerField(
        required=False, allow_null=True, min_value=1,
    )
    porcentaje = serializers.DecimalField(
        max_digits=7, decimal_places=4, required=False, allow_null=True,
    )
    monto = serializers.DecimalField(
        max_digits=18, decimal_places=2, required=False, allow_null=True,
    )


class AsignacionTerritorialSerializer(serializers.ModelSerializer):
    """Asignación territorial; los montos los calcula el servicio de reparto."""

    distrito_detalle = serializers.SerializerMethodField()

    class Meta:
        model = AsignacionTerritorial
        fields = [
            'id', 'distrito', 'distrito_detalle', 'poblacion', 'porcentaje',
            'monto_calculado', 'ajuste', 'monto_final',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'monto_calculado', 'ajuste', 'monto_final',
            'created_at', 'updated_at',
        ]

    def get_distrito_detalle(self, obj) -> dict | None:
        d = obj.distrito
        if d is None:
            return None
        return {'codigo': d.codigo, 'nombre': d.nombre}


class DistribucionTerritorialSerializer(serializers.ModelSerializer):
    """Distribución territorial con sus asignaciones anidadas.

    Escritura: `distritos` acepta [{distrito, poblacion?, porcentaje?,
    monto?}] y el viewset persiste las asignaciones. Los montos calculados
    (`monto_calculado`/`ajuste`/`monto_final`) los escribe el servicio.
    """

    gestion_anio = serializers.IntegerField(source='gestion.anio', read_only=True)
    metodo_display = serializers.CharField(
        source='get_metodo_display', read_only=True,
    )
    estado_display = serializers.CharField(
        source='get_estado_display', read_only=True,
    )
    fuente_detalle = serializers.SerializerMethodField()
    organismo_detalle = serializers.SerializerMethodField()
    asignaciones = AsignacionTerritorialSerializer(many=True, read_only=True)
    distritos = TerritorialAllocationInput(
        many=True, write_only=True, required=False,
    )
    total_asignado = serializers.SerializerMethodField()

    class Meta:
        model = DistribucionTerritorial
        fields = [
            'id', 'gestion', 'gestion_anio', 'version', 'fuente',
            'fuente_detalle', 'organismo', 'organismo_detalle', 'metodo',
            'metodo_display', 'bolsa_total', 'estado', 'estado_display',
            'observaciones', 'asignaciones', 'total_asignado', 'distritos',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'estado', 'estado_display', 'created_at', 'updated_at',
        ]
        extra_kwargs = {
            'version': {'required': False},
            'fuente': {'required': False},
            'organismo': {'required': False},
        }

    def get_fuente_detalle(self, obj) -> dict | None:
        return _detalle_catalogo(obj.fuente)

    def get_organismo_detalle(self, obj) -> dict | None:
        return _detalle_catalogo(obj.organismo)

    def get_total_asignado(self, obj) -> str:
        total = (
            obj.asignaciones.aggregate(monto_total=models.Sum('monto_final'))
            ['monto_total']
        )
        return str(total) if total is not None else '0.00'


# ---------------------------------------------------------------------------
# Fase 10 - Reformulaciones (cabecera + movimientos con saldos antes/después)
# ---------------------------------------------------------------------------
class ReformMovementInput(serializers.Serializer):
    """Fila de movimiento del payload de create (write-only, §92-97).

    Campos: {tipo, apertura_origen?, apertura_destino?, fuente?,
    organismo?, monto}. La estructura (aperturas de la gestión, monto > 0)
    la valida `services._validar_movimientos_reform`; la disponibilidad de
    saldos se valida al aplicar (`aplicar_reform`).
    """

    tipo = serializers.ChoiceField(choices=TipoMovimientoReform.CHOICES)
    apertura_origen = serializers.IntegerField(
        required=False, allow_null=True,
    )
    apertura_destino = serializers.IntegerField(
        required=False, allow_null=True,
    )
    fuente = serializers.UUIDField(required=False, allow_null=True)
    organismo = serializers.UUIDField(required=False, allow_null=True)
    monto = serializers.DecimalField(
        max_digits=18, decimal_places=2, min_value=Decimal('0.01'),
    )
    motivo = serializers.CharField(required=False, allow_blank=True,
                                   max_length=300)


def _detalle_apertura(apertura) -> dict | None:
    """{'id', 'denominacion', 'codigo_sisin'} de la apertura o None."""
    if apertura is None:
        return None
    return {
        'id': str(apertura.id),
        'denominacion': apertura.denominacion,
        'codigo_sisin': apertura.codigo_sisin or '',
    }


class ReformaMovimientoSerializer(serializers.ModelSerializer):
    """Movimiento de reformulación: lectura con detalles y saldos."""

    tipo_display = serializers.CharField(
        source='get_tipo_display', read_only=True,
    )
    apertura_origen_detalle = serializers.SerializerMethodField()
    apertura_destino_detalle = serializers.SerializerMethodField()
    fuente_detalle = serializers.SerializerMethodField()
    organismo_detalle = serializers.SerializerMethodField()

    class Meta:
        model = ReformaMovimiento
        fields = [
            'id', 'tipo', 'tipo_display', 'apertura_origen',
            'apertura_origen_detalle', 'apertura_destino',
            'apertura_destino_detalle', 'fuente', 'fuente_detalle',
            'organismo', 'organismo_detalle', 'monto', 'saldo_antes',
            'saldo_despues', 'motivo', 'created_at', 'updated_at',
        ]
        read_only_fields = fields

    def get_apertura_origen_detalle(self, obj) -> dict | None:
        return _detalle_apertura(obj.apertura_origen)

    def get_apertura_destino_detalle(self, obj) -> dict | None:
        return _detalle_apertura(obj.apertura_destino)

    def get_fuente_detalle(self, obj) -> dict | None:
        return _detalle_catalogo(obj.fuente)

    def get_organismo_detalle(self, obj) -> dict | None:
        return _detalle_catalogo(obj.organismo)


class ReformaSerializer(serializers.ModelSerializer):
    """Reformulación: cabecera + movimientos anidados.

    Escritura: `movimientos_input` acepta [{tipo, apertura_origen?,
    apertura_destino?, fuente?, organismo?, monto, motivo?}]; el viewset
    delega la creación en `services.crear_reform` (transacción + validación
    de gestión/distribución fijada). Lectura: `movimientos` con detalles y
    saldos.
    """

    gestion_anio = serializers.IntegerField(source='gestion.anio', read_only=True)
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    estado_display = serializers.CharField(
        source='get_estado_display', read_only=True,
    )
    solicitada_por_email = serializers.SerializerMethodField()
    aprobada_por_email = serializers.SerializerMethodField()
    version_origen_numero = serializers.SerializerMethodField()
    movimientos = ReformaMovimientoSerializer(many=True, read_only=True)

    class Meta:
        model = Reforma
        fields = [
            'id', 'gestion', 'gestion_anio', 'tipo', 'tipo_display',
            'estado', 'estado_display', 'motivo', 'resolucion',
            'documento', 'version_origen', 'version_origen_numero',
            'version_resultante', 'solicitada_por', 'solicitada_por_email',
            'aprobada_por', 'aprobada_por_email', 'fecha_aplicacion',
            'movimientos', 'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'estado', 'estado_display', 'version_origen',
            'version_origen_numero', 'version_resultante', 'solicitada_por',
            'aprobada_por', 'fecha_aplicacion', 'movimientos',
            'created_at', 'updated_at',
        ]
        extra_kwargs = {
            'gestion': {'required': True},
            'tipo': {'required': True},
            'documento': {'required': False, 'allow_null': True},
            'resolucion': {'required': False, 'allow_blank': True},
            'motivo': {'required': False, 'allow_blank': True},
        }

    def get_solicitada_por_email(self, obj) -> str | None:
        return obj.solicitada_por.email if obj.solicitada_por else None

    def get_aprobada_por_email(self, obj) -> str | None:
        return obj.aprobada_por.email if obj.aprobada_por else None

    def get_version_origen_numero(self, obj) -> int | None:
        return obj.version_origen.numero if obj.version_origen else None

    def to_internal_value(self, data):
        """Extrae `movimientos` del payload y valida cada fila (patrón
        `AperturaSerializer.fuentes`): la lectura `movimientos` sigue
        siendo read-only y la escritura viaja por el mismo nombre."""
        data = dict(data)
        movimientos_raw = data.pop('movimientos', None)
        validated = super().to_internal_value(data)
        if movimientos_raw is not None:
            if not isinstance(movimientos_raw, (list, tuple)):
                raise serializers.ValidationError({
                    'movimientos': 'Debe ser una lista de {tipo, '
                                   'apertura_origen, apertura_destino, '
                                   'fuente, organismo, monto}.',
                })
            entradas = []
            for i, fila in enumerate(movimientos_raw):
                serializador = ReformMovementInput(data=fila)
                if not serializador.is_valid():
                    raise serializers.ValidationError({
                        'movimientos': {i: serializador.errors},
                    })
                entradas.append(serializador.validated_data)
            validated['movimientos'] = entradas
        return validated


class AuditEventSerializer(serializers.ModelSerializer):
    """Evento de auditoría del ciclo presupuestario (Fase 11).

    Serializa `auditoria.EventoAuditoria` para la consulta de trazabilidad
    (GET /budget/audit/): usuario con email/nombre, acción con su etiqueta
    del catálogo, entidad con su etiqueta de dominio y los datos previos/
    posteriores tal cual se registraron (JSON).
    """

    usuario_email = serializers.EmailField(
        source='usuario.email', read_only=True, allow_null=True,
    )
    usuario_nombre = serializers.SerializerMethodField()
    accion_display = serializers.CharField(
        source='get_accion_display', read_only=True,
    )
    entidad_display = serializers.SerializerMethodField()
    # PIP-DB-008: gestion es FK a GestionFiscal; el contrato de la API expone
    # el AÑO en `gestion` (y el uuid queda disponible como gestion_id).
    gestion = serializers.SerializerMethodField()
    gestion_id = serializers.UUIDField(read_only=True, allow_null=True)

    ENTIDADES_DISPLAY = {
        'Apertura': 'Apertura programática',
        'Reserva': 'Reserva',
        'TechoVersion': 'Techo directivo',
        'DistribucionVersion': 'Distribución',
        'AsignacionObjetoGastoTecho': 'Objeto del gasto',
        'Reforma': 'Reformulación',
        'Importacion': 'Importación',
        'DistribucionTerritorial': 'Distribución territorial',
        'GestionFiscal': 'Gestión fiscal',
    }

    class Meta:
        model = EventoAuditoria
        fields = [
            'id', 'usuario', 'usuario_email', 'usuario_nombre', 'accion',
            'accion_display', 'entidad', 'entidad_display', 'entidad_id',
            'version', 'resumen', 'datos_previos', 'datos_posteriores',
            'direccion_ip', 'gestion', 'gestion_id', 'creado_en',
        ]

    def get_gestion(self, obj) -> int | None:
        return obj.gestion.anio if obj.gestion else None

    def get_usuario_nombre(self, obj) -> str:
        if obj.usuario is None:
            return 'Sistema'
        nombre = (
            f'{obj.usuario.first_name or ""} {obj.usuario.last_name or ""}'
        ).strip()
        return nombre or obj.usuario.email or 'Sistema'

    def get_entidad_display(self, obj) -> str:
        return self.ENTIDADES_DISPLAY.get(obj.entidad, obj.entidad)
