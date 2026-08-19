"""API V2 de techos presupuestarios del SIS-POA (WP módulo Presupuesto/Techos).

Contrato explícito sobre el modelo legacy TechoPresupuestario (plan §13.3).

DEPRECADA (TASK PIP-POA-001): la fuente canónica de techos directivos es
`budget.TechoDirectivo` (`/api/v2/sis-poa/budget/directive-ceilings/`,
ADR-005). Esta ruta responde con headers de deprecación blanda (RFC 8594) y
NO se retira hasta el Sunset documentado en `docs/refactor-pip/
LEGACY_DEPRECATION.md`. No tocar V1 ni `apps.budget`.
"""
from rest_framework import serializers, viewsets

from apps.accounts.permissions import TieneAlgunaCapacidad
from apps.techos.models import TechoPresupuestario

CAPACIDADES_ESCRITURA = ['sis_poa.budget.manage', 'sis_poa.formulate']

# Contrato de deprecación (TASK PIP-POA-001): BLANDA, con headers RFC 8594 y
# sin 410 inmediato (existen consumidores externos de la ruta). Sunset alineado
# con API V1 (2027-01-01) para un único hito de retiro; ver
# docs/refactor-pip/LEGACY_DEPRECATION.md §6.5.
DEPRECATION_SUNSET = 'Sun, 01 Jan 2027 00:00:00 GMT'
DEPRECATION_LINK = '/docs/refactor-pip/LEGACY_DEPRECATION.md'


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

    def finalize_response(self, request, response, *args, **kwargs):
        """Marca toda respuesta de la ruta legacy con headers RFC 8594.

        El contrato canónico es `directive-ceilings`; esta ruta queda
        operativa (deprecación blanda) hasta su Sunset.
        """
        response = super().finalize_response(request, response, *args, **kwargs)
        response['Deprecation'] = 'true'
        response['Sunset'] = DEPRECATION_SUNSET
        response['Link'] = f'<{DEPRECATION_LINK}>; rel="deprecation"'
        return response
