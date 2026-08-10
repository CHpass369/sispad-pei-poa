"""API V2 del SIS-PRO (WP-11 / /api/v2/sis-pro/)."""
from rest_framework import serializers, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.accounts.permissions import TieneAlgunaCapacidad
from apps.inversion.migration_v2 import cadena_ascendente
from apps.inversion.models_v2 import (
    CondicionPrevia,
    CostoProyecto,
    DocumentoTecnico,
    Proyecto,
    VinculoProyectoActividad,
)

CAPACIDADES_ESCRITURA = ['sis_pro.project.create', 'sis_pro.project.edit']
CAPACIDADES_VALIDACION = ['sis_pro.preinvestment.validate']


class ProyectoSerializer(serializers.ModelSerializer):
    geometry_geojson = serializers.SerializerMethodField()

    class Meta:
        model = Proyecto
        fields = '__all__'
        read_only_fields = [
            'id', 'puntaje_madurez', 'habilitado_poa',
            'created_at', 'updated_at',
        ]

    def get_geometry_geojson(self, obj):
        if not obj.geom:
            return None
        import json

        return json.loads(obj.geom.transform(4326, clone=True).geojson)


class CondicionSerializer(serializers.ModelSerializer):
    class Meta:
        model = CondicionPrevia
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class DocumentoSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentoTecnico
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class CostoSerializer(serializers.ModelSerializer):
    class Meta:
        model = CostoProyecto
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class VinculoSerializer(serializers.ModelSerializer):
    actividad_codigo = serializers.CharField(
        source='actividad.codigo', read_only=True,
    )

    class Meta:
        model = VinculoProyectoActividad
        fields = [
            'id', 'proyecto', 'actividad', 'actividad_codigo',
            'es_principal', 'justificacion', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']


def _permisos(*capacidades):
    return [TieneAlgunaCapacidad(*capacidades)]


class ProyectoViewSet(viewsets.ModelViewSet):
    queryset = Proyecto.objects.select_related('ue')
    serializer_class = ProyectoSerializer
    filterset_fields = ['gestion', 'fase', 'estado']

    def get_permissions(self):
        if self.action in ('create', 'update', 'partial_update', 'destroy'):
            return _permisos(*CAPACIDADES_ESCRITURA)
        return super().get_permissions()

    @action(detail=True, methods=['get'])
    def cadena(self, request, pk=None):
        """Cadena ascendente Proyecto → POA → PEI → marco superior."""
        return Response(cadena_ascendente(self.get_object()))

    @action(detail=True, methods=['post'])
    def avanzar_fase(self, request, pk=None):
        proyecto = self.get_object()
        if not TieneAlgunaCapacidad(*CAPACIDADES_VALIDACION).has_permission(
            request, self,
        ):
            from rest_framework import status
            return Response(
                {'error': 'Requiere la capacidad sis_pro.preinvestment.validate'},
                status=status.HTTP_403_FORBIDDEN,
            )
        ok, resultado = proyecto.avanzar_fase()
        if not ok:
            from rest_framework import status
            return Response(
                {'error': resultado}, status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(ProyectoSerializer(proyecto).data)

    @action(detail=True, methods=['get'])
    def presupuesto(self, request, pk=None):
        proyecto = self.get_object()
        costos = sum(
            (c.monto for c in proyecto.costos.all()), 0,
        )
        return Response({
            'costo_total': str(proyecto.costo_total),
            'ejecucion_acumulada': str(proyecto.ejecucion_acumulada),
            'saldo': str(proyecto.costo_total - proyecto.ejecucion_acumulada),
            'costos_detalle': str(costos),
        })

    @action(detail=True, methods=['get'])
    def condiciones(self, request, pk=None):
        serializer = CondicionSerializer(
            self.get_object().condiciones_previas.all(), many=True,
        )
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def documentos(self, request, pk=None):
        serializer = DocumentoSerializer(
            self.get_object().documentos_tecnicos.all(), many=True,
        )
        return Response(serializer.data)


class CondicionViewSet(viewsets.ModelViewSet):
    queryset = CondicionPrevia.objects.select_related('proyecto')
    serializer_class = CondicionSerializer
    filterset_fields = ['proyecto', 'cumplida']

    def get_permissions(self):
        if self.action in ('create', 'update', 'partial_update', 'destroy'):
            return _permisos(*CAPACIDADES_ESCRITURA)
        return super().get_permissions()


class DocumentoViewSet(viewsets.ModelViewSet):
    queryset = DocumentoTecnico.objects.select_related('proyecto')
    serializer_class = DocumentoSerializer
    filterset_fields = ['proyecto', 'tipo', 'estado']

    def get_permissions(self):
        if self.action in ('create', 'update', 'partial_update', 'destroy'):
            return _permisos(*CAPACIDADES_ESCRITURA)
        return super().get_permissions()


class CostoViewSet(viewsets.ModelViewSet):
    queryset = CostoProyecto.objects.select_related('proyecto')
    serializer_class = CostoSerializer
    filterset_fields = ['proyecto', 'anio']

    def get_permissions(self):
        if self.action in ('create', 'update', 'partial_update', 'destroy'):
            return _permisos(*CAPACIDADES_ESCRITURA)
        return super().get_permissions()


class VinculoViewSet(viewsets.ModelViewSet):
    queryset = VinculoProyectoActividad.objects.select_related(
        'proyecto', 'actividad',
    )
    serializer_class = VinculoSerializer
    filterset_fields = ['proyecto', 'actividad']

    def get_permissions(self):
        if self.action in ('create', 'update', 'partial_update', 'destroy'):
            return _permisos(*CAPACIDADES_ESCRITURA)
        return super().get_permissions()
