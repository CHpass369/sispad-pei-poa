"""API V2 de techos presupuestarios del SIS-POA.

El techo es el parámetro madre de cada año fiscal: se compone de recursos
(ingresos por fuente/organismo/concepto) y reservas de gastos obligatorios.
La distribución por categorías programáticas no puede exceder el saldo
disponible del techo.
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
    resumen_techo,
    validar_distribucion_no_excede,
)

CAPACIDADES_ESCRITURA = ['sis_poa.budget.manage', 'sis_poa.formulate']
CAPACIDADES_LECTURA = ['sis_poa.budget.manage', 'sis_poa.formulate', 'sis_poa.project.read']


class TechoSerializerV2(serializers.ModelSerializer):
    fuente_codigo = serializers.CharField(source='fuente.codigo', read_only=True)
    fuente_nombre = serializers.CharField(source='fuente.denominacion', read_only=True)
    total_recursos = serializers.DecimalField(
        max_digits=20, decimal_places=2, read_only=True,
    )
    total_gastos_obligatorios = serializers.DecimalField(
        max_digits=20, decimal_places=2, read_only=True,
    )
    monto_distribuido = serializers.DecimalField(
        max_digits=20, decimal_places=2, read_only=True,
    )
    saldo_disponible = serializers.DecimalField(
        max_digits=20, decimal_places=2, read_only=True,
    )

    class Meta:
        model = TechoPresupuestario
        fields = [
            'id', 'gestion', 'monto_total', 'fuente', 'fuente_codigo',
            'fuente_nombre', 'organismo', 'concepto', 'descripcion', 'activo',
            'total_recursos', 'total_gastos_obligatorios',
            'monto_distribuido', 'saldo_disponible',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['total_recursos'] = instance.total_recursos
        data['total_gastos_obligatorios'] = instance.total_gastos_obligatorios
        data['monto_distribuido'] = instance.monto_distribuido
        data['saldo_disponible'] = instance.saldo_disponible
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


class _PermisoEscrituraMixin:
    def get_permissions(self):
        if self.action in ('create', 'update', 'partial_update', 'destroy'):
            return [TieneAlgunaCapacidad(*CAPACIDADES_ESCRITURA)]
        return super().get_permissions()


class TechoViewSetV2(_PermisoEscrituraMixin, viewsets.ModelViewSet):
    queryset = TechoPresupuestario.objects.select_related('fuente', 'organismo')
    serializer_class = TechoSerializerV2
    filterset_fields = ['gestion', 'activo']

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


class RecursoTechoViewSetV2(_PermisoEscrituraMixin, viewsets.ModelViewSet):
    queryset = RecursoTecho.objects.select_related('techo', 'fuente', 'organismo')
    serializer_class = RecursoTechoSerializer
    filterset_fields = ['techo', 'fuente']


class GastoObligatorioViewSetV2(_PermisoEscrituraMixin, viewsets.ModelViewSet):
    queryset = GastoObligatorio.objects.select_related(
        'techo', 'da', 'ue', 'programa', 'fuente', 'organismo', 'objeto_gasto',
    )
    serializer_class = GastoObligatorioSerializer
    filterset_fields = ['techo', 'fuente', 'activo']
