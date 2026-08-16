"""Vistas V2 del kernel estratégico SIS-PE (WP-04 / ADR-002).

Escritura protegida por capacidades (ADR-003); lectura para cualquier
usuario autenticado. Las versiones aprobadas son inmutables (modelo).
"""
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.accounts.permissions import TieneAlgunaCapacidad
from apps.planificacion.models_v2 import (
    EstadosInstrumento,
    InstrumentoPlanificacion,
    NodoEstrategico,
    TipoInstrumento,
    TipoNodoEstrategico,
    TipoVinculoEstrategico,
    VersionInstrumento,
    VersionMetodologia,
    VinculoEstrategico,
)
from apps.planificacion.serializers_v2 import (
    InstrumentoSerializer,
    NodoEstrategicoSerializer,
    TipoInstrumentoSerializer,
    TipoNodoEstrategicoSerializer,
    TipoVinculoEstrategicoSerializer,
    VersionInstrumentoSerializer,
    VersionMetodologiaSerializer,
    VinculoEstrategicoSerializer,
)

CAPACIDADES_LECTURA = []
CAPACIDADES_ESCRITURA_INSTRUMENTO = ['sis_pe.instrumento.create']
CAPACIDADES_ESCRITURA_NODO = [
    'sis_pe.pad.edit', 'sis_pe.pei.edit', 'sis_pe.articulacion.manage',
]


class InstrumentoViewSet(viewsets.ModelViewSet):
    queryset = InstrumentoPlanificacion.objects.select_related('tipo')
    serializer_class = InstrumentoSerializer
    ordering = ['-id']

    def get_permissions(self):
        if self.action in ('create', 'update', 'partial_update', 'destroy'):
            return [TieneAlgunaCapacidad(*CAPACIDADES_ESCRITURA_INSTRUMENTO)]
        return super().get_permissions()

    def get_queryset(self):
        qs = super().get_queryset()
        tipo = self.request.query_params.get('tipo')
        if tipo:
            qs = qs.filter(tipo_id=tipo)
        return qs

    def _with_counts(self, qs):
        from django.db.models import Count
        return qs.annotate(
            versiones_count=Count('versiones', distinct=True),
        )

    def list(self, request, *args, **kwargs):
        queryset = self._with_counts(self.filter_queryset(self.get_queryset()))
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        obj = self.get_object()
        serializer = self.get_serializer(obj)
        data = serializer.data
        data['versiones_count'] = obj.versiones.count()
        return Response(data)

    @action(detail=True, methods=['post'])
    def crear_version(self, request, pk=None):
        """Crea la siguiente versión del instrumento con una metodología."""
        instrumento = self.get_object()
        metodologia_id = request.data.get('metodologia')
        if not metodologia_id:
            return Response(
                {'error': 'El campo "metodologia" es requerido'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        metodologia = VersionMetodologia.objects.filter(pk=metodologia_id).first()
        if not metodologia:
            return Response(
                {'error': 'Metodología no encontrada'},
                status=status.HTTP_404_NOT_FOUND,
            )
        ultimo = instrumento.versiones.order_by('numero').last()
        version = VersionInstrumento.objects.create(
            instrumento=instrumento,
            numero=(ultimo.numero + 1) if ultimo else 1,
            metodologia=metodologia,
            etiqueta=request.data.get('etiqueta', ''),
        )
        serializer = VersionInstrumentoSerializer(version)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get'])
    def versiones(self, request, pk=None):
        instrumento = self.get_object()
        versiones = instrumento.versiones.select_related(
            'instrumento', 'metodologia',
        ).order_by('numero')
        serializer = VersionInstrumentoSerializer(versiones, many=True)
        return Response(serializer.data)


class VersionViewSet(viewsets.ReadOnlyModelViewSet):
    """Versiones de instrumento (lectura + acciones de estado)."""

    queryset = VersionInstrumento.objects.select_related(
        'instrumento', 'metodologia',
    )
    serializer_class = VersionInstrumentoSerializer

    def get_permissions(self):
        if self.action in ('aprobar',):
            return [TieneAlgunaCapacidad(*CAPACIDADES_ESCRITURA_NODO)]
        return super().get_permissions()

    @action(detail=True, methods=['post'])
    def aprobar(self, request, pk=None):
        """Aprueba la versión: inmutable + checksum + norma."""
        version = self.get_object()
        if version.inmutable:
            return Response(
                {'error': 'La versión ya está aprobada y es inmutable.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not version.nodos.exists():
            return Response(
                {'error': 'No se puede aprobar una versión sin nodos.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        version.aprobar(
            usuario=request.user,
            norma=request.data.get('norma_aprobacion', ''),
        )
        serializer = VersionInstrumentoSerializer(version)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def nodos(self, request, pk=None):
        version = self.get_object()
        nodos = version.nodos.select_related('tipo_nodo', 'padre').order_by(
            'orden', 'codigo',
        )
        serializer = NodoEstrategicoSerializer(nodos, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def vinculos(self, request, pk=None):
        version = self.get_object()
        vinculos = version.vinculos.select_related(
            'tipo', 'origen', 'destino',
        )
        serializer = VinculoEstrategicoSerializer(vinculos, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def verificar(self, request, pk=None):
        """Verifica el checksum de datos de la versión."""
        version = self.get_object()
        return Response({
            'id': str(version.id),
            'inmutable': version.inmutable,
            'checksum_registrado': version.checksum,
            'checksum_actual': version.calcular_checksum(),
            'consistente': version.verificar_checksum(),
        })


class NodoViewSet(viewsets.ModelViewSet):
    queryset = NodoEstrategico.objects.select_related('tipo_nodo', 'padre')
    serializer_class = NodoEstrategicoSerializer

    def get_permissions(self):
        if self.action in ('create', 'update', 'partial_update', 'destroy'):
            return [TieneAlgunaCapacidad(*CAPACIDADES_ESCRITURA_NODO)]
        return super().get_permissions()


class VinculoViewSet(viewsets.ModelViewSet):
    queryset = VinculoEstrategico.objects.select_related(
        'tipo', 'origen', 'destino',
    )
    serializer_class = VinculoEstrategicoSerializer

    def get_permissions(self):
        if self.action in ('create', 'update', 'partial_update', 'destroy'):
            return [TieneAlgunaCapacidad(*CAPACIDADES_ESCRITURA_NODO)]
        return super().get_permissions()


class TipoInstrumentoViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = TipoInstrumento.objects.all()
    serializer_class = TipoInstrumentoSerializer


class MetodologiaViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = VersionMetodologia.objects.select_related('tipo_instrumento')
    serializer_class = VersionMetodologiaSerializer

    @action(detail=True, methods=['get'])
    def tipos_nodo(self, request, pk=None):
        metodologia = self.get_object()
        serializer = TipoNodoEstrategicoSerializer(
            metodologia.tipos_nodo.filter(activo=True), many=True,
        )
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def tipos_vinculo(self, request, pk=None):
        metodologia = self.get_object()
        serializer = TipoVinculoEstrategicoSerializer(
            metodologia.tipos_vinculo.filter(activo=True), many=True,
        )
        return Response(serializer.data)
