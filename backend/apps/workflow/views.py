from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import EnvioFormulacion, Revision, Observacion, Aprobacion
from .serializers import (
    EnvioFormulacionSerializer, RevisionSerializer,
    ObservacionSerializer, AprobacionSerializer
)


class EnvioFormulacionViewSet(viewsets.ModelViewSet):
    queryset = EnvioFormulacion.objects.all()
    serializer_class = EnvioFormulacionSerializer
    filterset_fields = ['unidad', 'gestion', 'activo']

    @action(detail=True, methods=['post'])
    def devolver(self, request, pk=None):
        envio = self.get_object()
        revision = Revision.objects.create(
            envio=envio,
            tipo_revision=request.data.get('tipo_revision', 'planificacion'),
            revisor=request.user,
            estado='devuelta',
            resultado='observado',
        )
        observacion = Observacion.objects.create(
            codigo=f'OBS-{envio.unidad.codigo}-{envio.gestion}-{Observacion.objects.count() + 1}',
            revision=revision,
            tipo=request.data.get('tipo', 'tecnica'),
            severidad=request.data.get('severidad', 'moderada'),
            modulo=request.data.get('modulo', 'general'),
            registro_id=str(envio.id),
            texto=request.data.get('texto', ''),
            responsable_subsanacion_id=request.data.get('responsable_id'),
            gestion=envio.gestion,
        )
        return Response(ObservacionSerializer(observacion).data, status=status.HTTP_201_CREATED)


class RevisionViewSet(viewsets.ModelViewSet):
    queryset = Revision.objects.all()
    serializer_class = RevisionSerializer
    filterset_fields = ['envio', 'tipo_revision', 'estado', 'revisor']


class ObservacionViewSet(viewsets.ModelViewSet):
    queryset = Observacion.objects.all()
    serializer_class = ObservacionSerializer
    filterset_fields = ['revision', 'estado', 'tipo', 'severidad', 'gestion']

    @action(detail=True, methods=['post'])
    def subsanar(self, request, pk=None):
        obs = self.get_object()
        obs.respuesta = request.data.get('respuesta', '')
        obs.evidencia_subsanacion = request.data.get('evidencia', '')
        obs.estado = 'respondida'
        obs.save()
        return Response(ObservacionSerializer(obs).data)


class AprobacionViewSet(viewsets.ModelViewSet):
    queryset = Aprobacion.objects.all()
    serializer_class = AprobacionSerializer
    filterset_fields = ['gestion', 'tipo', 'estado']


class ConsolidacionViewSet(viewsets.ViewSet):
    """ViewSet para operaciones de consolidación presupuestaria."""

    @action(detail=False, methods=['post'])
    def consolidar(self, request):
        """Ejecuta consolidación para una gestión específica.

        POST /api/v1/consolidacion/consolidar/
        Body: {"gestion": 2026}
        """
        gestion = request.data.get('gestion')
        if not gestion:
            return Response(
                {'error': 'El parámetro "gestion" es requerido'},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            from .consolidacion import consolidar_poa_institucional
            resultado = consolidar_poa_institucional(gestion)
            return Response(resultado, status=status.HTTP_200_OK)
        except ImportError:
            return Response(
                {'error': 'El módulo de consolidación no está disponible'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

    @action(detail=False, methods=['get'])
    def reporte(self, request):
        """Obtiene resultados de consolidación para una gestión.

        GET /api/v1/consolidacion/reporte/?gestion=2026
        """
        gestion = request.query_params.get('gestion')
        if not gestion:
            return Response(
                {'error': 'El parámetro "gestion" es requerido'},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            from .consolidacion import consolidar_poa_institucional
            resultado = consolidar_poa_institucional(gestion)
            return Response(resultado)
        except ImportError:
            return Response(
                {'error': 'El módulo de consolidación no está disponible'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

    @action(detail=False, methods=['get'])
    def verificar(self, request):
        """Verifica consistencia presupuestaria para una gestión.

        GET /api/v1/consolidacion/verificar/?gestion=2026
        """
        gestion = request.query_params.get('gestion')
        if not gestion:
            return Response(
                {'error': 'El parámetro "gestion" es requerido'},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            from .consolidacion import verificar_consistencia_presupuestaria
            resultado = verificar_consistencia_presupuestaria(gestion)
            return Response(resultado)
        except ImportError:
            return Response(
                {'error': 'El módulo de consolidación no está disponible'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

    @action(detail=False, methods=['get'])
    def acta(self, request):
        """Genera acta de consolidación para una gestión.

        GET /api/v1/consolidacion/acta/?gestion=2026
        """
        gestion = request.query_params.get('gestion')
        if not gestion:
            return Response(
                {'error': 'El parámetro "gestion" es requerido'},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            from .consolidacion import generar_acta_consolidacion
            resultado = generar_acta_consolidacion(gestion)
            return Response(resultado)
        except ImportError:
            return Response(
                {'error': 'El módulo de consolidación no está disponible'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
