from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Prefetch

from .models import (
    SectorPAD, PoliticaPAD, LineamientoEstrategico,
    ResultadoTerritorial, ProductoTerritorial, ArticulacionSIPEB,
    ProgramacionAnualPAD,
)
from .serializers import (
    SectorPADSerializer, PoliticaPADSerializer,
    LineamientoEstrategicoSerializer, ResultadoTerritorialSerializer,
    ResultadoTerritorialListSerializer, ProductoTerritorialSerializer,
    ArticulacionSIPEBSerializer, ProgramacionAnualPADSerializer,
)
from apps.planificacion.models import NodoPlanificacion, AccionCortoPlazo


class SectorPADViewSet(viewsets.ModelViewSet):
    queryset = SectorPAD.objects.all()
    serializer_class = SectorPADSerializer
    search_fields = ['codigo', 'nombre']
    ordering_fields = ['codigo', 'nombre']


class PoliticaPADViewSet(viewsets.ModelViewSet):
    queryset = PoliticaPAD.objects.all()
    serializer_class = PoliticaPADSerializer
    filterset_fields = ['gestion']
    search_fields = ['codigo', 'nombre']
    ordering_fields = ['gestion', 'codigo']


class LineamientoEstrategicoViewSet(viewsets.ModelViewSet):
    queryset = LineamientoEstrategico.objects.select_related('politica').all()
    serializer_class = LineamientoEstrategicoSerializer
    filterset_fields = ['gestion', 'politica']
    search_fields = ['codigo', 'nombre']
    ordering_fields = ['gestion', 'codigo']

    @action(detail=False, methods=['get'])
    def por_politica(self, request):
        """Agrupa lineamientos por política"""
        politica_id = request.query_params.get('politica_id')
        if politica_id:
            qs = self.get_queryset().filter(politica_id=politica_id)
        else:
            qs = self.get_queryset()
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)


class ResultadoTerritorialViewSet(viewsets.ModelViewSet):
    queryset = ResultadoTerritorial.objects.select_related(
        'lineamiento', 'sector'
    ).prefetch_related(
        Prefetch('productos', queryset=ProductoTerritorial.objects.all()),
        'articulacion_sipeb',
        'programaciones',
    ).all()

    filterset_fields = ['gestion', 'lineamiento', 'sector']
    search_fields = ['codigo', 'nombre', 'indicador']
    ordering_fields = ['gestion', 'codigo']

    def get_serializer_class(self):
        if self.action == 'list':
            return ResultadoTerritorialListSerializer
        return ResultadoTerritorialSerializer

    @action(detail=True, methods=['get'])
    def productos(self, request, pk=None):
        """Retorna los productos de un resultado territorial"""
        resultado = self.get_object()
        productos = resultado.productos.all()
        serializer = ProductoTerritorialSerializer(productos, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def por_lineamiento(self, request):
        """Filtra resultados por lineamiento"""
        lineamiento_id = request.query_params.get('lineamiento_id')
        if not lineamiento_id:
            return Response(
                {'error': 'lineamiento_id es requerido'},
                status=status.HTTP_400_BAD_REQUEST
            )
        qs = self.get_queryset().filter(lineamiento_id=lineamiento_id)
        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def cadena_completa(self, request, pk=None):
        """Devuelve la cadena: PGDESA → PDESA → PDS → PAD → PEI → POA

        Integra la articulación SIPEB de un resultado territorial con los
        instrumentos de planificación municipal (PEI → POA).
        """
        resultado = self.get_object()

        # Datos del PAD (resultado + articulación + productos)
        serializer = ResultadoTerritorialSerializer(resultado)
        data = serializer.data

        # Buscar articulación en PEI: nodos de planificación que referencien
        # este código de resultado. Enlace semántico por código + gestión.
        gestion = resultado.gestion
        pei_nodos = NodoPlanificacion.objects.filter(
            plan__tipo='pei',
            plan__gestion_inicio__lte=gestion,
            plan__gestion_fin__gte=gestion,
            codigo__icontains=resultado.codigo,
        ).values('id', 'codigo', 'nombre', 'nivel')

        data['pei'] = list(pei_nodos)

        # Buscar acciones de corto plazo (POA) vinculadas
        if pei_nodos.exists():
            nodo_ids = [n['id'] for n in pei_nodos]
            poa_acciones = AccionCortoPlazo.objects.filter(
                accion_mediano_plazo__nodo_planificacion_id__in=nodo_ids,
                gestion=gestion,
            ).select_related(
                'unidad_responsable'
            ).values(
                'id', 'codigo', 'nombre', 'gestion',
                'unidad_responsable__nombre',
            )
            data['poa'] = [
                {
                    'id': a['id'],
                    'codigo': a['codigo'],
                    'nombre': a['nombre'],
                    'gestion': a['gestion'],
                    'unidad_responsable': a['unidad_responsable__nombre'],
                }
                for a in poa_acciones
            ]
        else:
            data['poa'] = []

        return Response(data)


class ProductoTerritorialViewSet(viewsets.ModelViewSet):
    queryset = ProductoTerritorial.objects.select_related('resultado').all()
    serializer_class = ProductoTerritorialSerializer
    filterset_fields = ['gestion', 'resultado']
    search_fields = ['codigo', 'nombre']
    ordering_fields = ['gestion', 'codigo']


class ArticulacionSIPEBViewSet(viewsets.ModelViewSet):
    queryset = ArticulacionSIPEB.objects.select_related('resultado').all()
    serializer_class = ArticulacionSIPEBSerializer
    filterset_fields = ['gestion', 'resultado']
    search_fields = [
        'cod_eje_pgdesa', 'cod_componente_pdesa',
        'cod_ods', 'cod_sector',
    ]


class ProgramacionAnualPADViewSet(viewsets.ModelViewSet):
    queryset = ProgramacionAnualPAD.objects.select_related(
        'resultado', 'producto'
    ).all()
    serializer_class = ProgramacionAnualPADSerializer
    filterset_fields = ['anio', 'tipo', 'resultado', 'producto']
    ordering_fields = ['anio', 'tipo', 'valor']
