"""API V2 de techos presupuestarios del SIS-POA (WP módulo Presupuesto/Techos).

Contrato explícito sobre el modelo canónico TechoPresupuestario (plan §13.3:
recursos + techos + presupuesto bajo dominio funcional SIS-POA).
"""
from rest_framework import serializers, viewsets

from apps.accounts.permissions import TieneAlgunaCapacidad
from apps.techos.models import TechoPresupuestario

CAPACIDADES_ESCRITURA = ['sis_poa.budget.manage', 'sis_poa.formulate']


class TechoSerializerV2(serializers.ModelSerializer):
    fuente_codigo = serializers.CharField(source='fuente.codigo', read_only=True)
    fuente_nombre = serializers.CharField(source='fuente.denominacion', read_only=True)

    class Meta:
        model = TechoPresupuestario
        fields = [
            'id', 'gestion', 'monto_total', 'fuente', 'fuente_codigo',
            'fuente_nombre', 'organismo', 'descripcion', 'activo',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class TechoViewSetV2(viewsets.ModelViewSet):
    queryset = TechoPresupuestario.objects.select_related('fuente', 'organismo')
    serializer_class = TechoSerializerV2
    filterset_fields = ['gestion', 'activo']

    def get_permissions(self):
        if self.action in ('create', 'update', 'partial_update', 'destroy'):
            return [TieneAlgunaCapacidad(*CAPACIDADES_ESCRITURA)]
        return super().get_permissions()
