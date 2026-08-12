"""API V2 de techos presupuestarios del SIS-POA.

El techo es el parámetro madre de cada año fiscal: se compone de recursos
(ingresos por fuente/organismo/concepto) y reservas de gastos obligatorios.
La distribución por categorías programáticas no puede exceder el saldo
disponible del techo.

Permisos (design §11): la LECTURA de datos financieros exige al menos una
capacidad de CAPACIDADES_LECTURA (`sis_poa.budget.manage`,
`sis_poa.formulate` o `sis_poa.project.read`); la escritura exige
CAPACIDADES_ESCRITURA. Sin la aplicación explícita, el fallback DRF
(IsAuthenticated) dejaría leer datos financieros a cualquier usuario
autenticado (K4 4R).
"""
from decimal import Decimal

from rest_framework import serializers, viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.accounts.permissions import TieneAlgunaCapacidad
from apps.techos.models import (
    GastoObligatorio,
    RecursoTecho,
    TechoPresupuestario,
)
from apps.techos.services import (
    budget_service,
    resumen_techo,
    validar_distribucion_no_excede,
)

CAPACIDADES_ESCRITURA = ['sis_poa.budget.manage', 'sis_poa.formulate']
CAPACIDADES_LECTURA = ['sis_poa.budget.manage', 'sis_poa.formulate', 'sis_poa.project.read']


def _decimal_str(valor) -> str:
    """Serializa Decimal a string con 2 decimales (convención del proyecto).

    Misma salida que un DecimalField read_only de DRF ("238826101.00"):
    nunca Decimal crudo en JSON (K3 4R, K1/K2 pins dependen del string).
    """
    return str(Decimal(valor).quantize(Decimal('0.01')))


class TechoSerializerV2(serializers.ModelSerializer):
    fuente_codigo = serializers.CharField(source='fuente.codigo', read_only=True)
    fuente_nombre = serializers.CharField(source='fuente.denominacion', read_only=True)

    class Meta:
        model = TechoPresupuestario
        fields = [
            'id', 'gestion', 'gestion_fiscal', 'monto_total', 'fuente',
            'fuente_codigo', 'fuente_nombre', 'organismo', 'concepto',
            'descripcion', 'activo',
            'total_recursos', 'total_gastos_obligatorios',
            'monto_distribuido', 'saldo_disponible',
            'created_at', 'updated_at',
        ]
        # monto_total es columna legacy read-only (Q1/DD6): la
        # data-migration 0004 lo recalcula como SUM(RecursoTecho.monto) y
        # toda consulta deriva de total_recursos (K3b 4R).
        read_only_fields = ['id', 'monto_total', 'created_at', 'updated_at']

    def validate(self, attrs):
        """Cross-gestión (design §12): gestion == gestion_fiscal.anio."""
        gestion = attrs.get('gestion', getattr(self.instance, 'gestion', None))
        gestion_fiscal = attrs.get(
            'gestion_fiscal', getattr(self.instance, 'gestion_fiscal', None),
        )
        if (
            gestion is not None
            and gestion_fiscal is not None
            and gestion != gestion_fiscal.anio
        ):
            raise serializers.ValidationError({
                'gestion_fiscal': (
                    f'La gestión del techo ({gestion}) no coincide con la '
                    f'gestión fiscal asociada ({gestion_fiscal.anio}).'
                ),
            })
        return attrs

    def create(self, validated_data):
        # monto_total es read_only (Q1/DD6); al crear el techo todavía no
        # hay recursos: la columna legacy nace en 0 y se reconcilia cuando
        # la API de recursos/clasificación (S4) mantiene
        # monto_total = SUM(RecursoTecho.monto).
        validated_data.setdefault('monto_total', Decimal('0.00'))
        return super().create(validated_data)

    def to_representation(self, instance):
        """Una sola vía de serialización de los agregados (K3c 4R).

        En listado usa el resumen BATCH del servicio (resumen_techos, W8)
        inyectado por el viewset en el context; en detail/fallback cae al
        motor por-techo (get_techo_resumen). Nunca Decimal crudo: los
        agregados salen como strings con 2 decimales (convención).
        """
        data = super().to_representation(instance)
        resumen = self.context.get('resumen_techos')
        if resumen is not None:
            r = resumen.get(str(instance.id))
            if r is not None:
                data['total_recursos'] = _decimal_str(r['total_recursos'])
                data['total_gastos_obligatorios'] = _decimal_str(
                    r['total_gastos_obligatorios'],
                )
                data['monto_distribuido'] = _decimal_str(r['monto_distribuido'])
                data['saldo_disponible'] = _decimal_str(r['saldo_disponible'])
                return data
        data['total_recursos'] = _decimal_str(instance.total_recursos)
        data['total_gastos_obligatorios'] = _decimal_str(
            instance.total_gastos_obligatorios,
        )
        data['monto_distribuido'] = _decimal_str(instance.monto_distribuido)
        data['saldo_disponible'] = _decimal_str(instance.saldo_disponible)
        return data


class RecursoTechoSerializer(serializers.ModelSerializer):
    fuente_codigo = serializers.CharField(source='fuente.codigo', read_only=True)
    fuente_nombre = serializers.CharField(source='fuente.denominacion', read_only=True)
    organismo_codigo = serializers.CharField(source='organismo.codigo', read_only=True, default=None)

    class Meta:
        model = RecursoTecho
        fields = [
            'id', 'techo', 'rubro', 'rubro_descripcion', 'fuente',
            'fuente_codigo', 'fuente_nombre', 'organismo', 'organismo_codigo',
            'entidad_otorgante', 'concepto', 'monto', 'orden',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class GastoObligatorioSerializer(serializers.ModelSerializer):
    fuente_codigo = serializers.CharField(source='fuente.codigo', read_only=True)
    fuente_nombre = serializers.CharField(source='fuente.denominacion', read_only=True)
    programa_codigo = serializers.CharField(source='programa.codigo', read_only=True, default=None)

    class Meta:
        model = GastoObligatorio
        fields = [
            'id', 'techo', 'da', 'ue', 'programa', 'programa_codigo',
            'fuente', 'fuente_codigo', 'fuente_nombre', 'organismo',
            'objeto_gasto', 'denominacion', 'base_legal', 'monto',
            'activo', 'orden', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class _PermisoTechoMixin:
    """Lectura: al menos una capacidad de CAPACIDADES_LECTURA (design §11).

    Aplica a list/retrieve y a los actions de lectura (resumen,
    control_distribucion); la escritura exige CAPACIDADES_ESCRITURA. El
    fallback DRF (IsAuthenticated) dejaría leer datos financieros a
    cualquier usuario autenticado (K4 4R).
    """

    def get_permissions(self):
        if self.action in ('create', 'update', 'partial_update', 'destroy'):
            return [TieneAlgunaCapacidad(*CAPACIDADES_ESCRITURA)]
        return [TieneAlgunaCapacidad(*CAPACIDADES_LECTURA)]


class TechoViewSetV2(_PermisoTechoMixin, viewsets.ModelViewSet):
    queryset = TechoPresupuestario.objects.select_related('fuente', 'organismo')
    serializer_class = TechoSerializerV2
    filterset_fields = ['gestion', 'activo']

    def list(self, request, *args, **kwargs):
        """Listado sin N+1 (W8): un solo resumen batch por página.

        Contrato W8: resumen_techos(qs) produce el MISMO dict por techo
        que get_techo_resumen (mismas claves y ecuación D11), con 3 SUMs
        agrupados en vez de 4 SUMs por techo. El serializer lo lee del
        context; en detail/fallback usa el motor por-techo.
        """
        qs = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(qs)
        resumen = budget_service.resumen_techos(page if page is not None else qs)
        context = {**self.get_serializer_context(), 'resumen_techos': resumen}
        serializer = self.get_serializer(
            page if page is not None else qs,
            many=True,
            context=context,
        )
        if page is not None:
            return self.get_paginated_response(serializer.data)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def resumen(self, request, pk=None):
        techo = self.get_object()
        return Response(resumen_techo(techo))

    @action(detail=True, methods=['get'])
    def control_distribucion(self, request, pk=None):
        techo = self.get_object()
        monto = request.query_params.get('monto')
        try:
            monto = Decimal(monto or '0')
        except Exception:
            return Response({'error': 'monto inválido'}, status=status.HTTP_400_BAD_REQUEST)
        return Response(validar_distribucion_no_excede(techo, monto))


class RecursoTechoViewSetV2(_PermisoTechoMixin, viewsets.ModelViewSet):
    queryset = RecursoTecho.objects.select_related('techo', 'fuente', 'organismo')
    serializer_class = RecursoTechoSerializer
    filterset_fields = ['techo', 'fuente']


class GastoObligatorioViewSetV2(_PermisoTechoMixin, viewsets.ModelViewSet):
    queryset = GastoObligatorio.objects.select_related(
        'techo', 'da', 'ue', 'programa', 'fuente', 'organismo', 'objeto_gasto',
    )
    serializer_class = GastoObligatorioSerializer
    filterset_fields = ['techo', 'fuente', 'activo']
