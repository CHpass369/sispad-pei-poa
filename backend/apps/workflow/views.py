from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import EnvioFormulacion, Revision, Observacion, Aprobacion
from .serializers import (
    EnvioFormulacionSerializer, RevisionSerializer,
    ObservacionSerializer, AprobacionSerializer
)
from .services import verificar_permisos_estado


def _verificar_transicion(usuario, envio, accion):
    resultado = verificar_permisos_estado(usuario, envio.estado_anterior, accion)
    if not resultado['permitido']:
        return resultado
    return None


class EnvioFormulacionViewSet(viewsets.ModelViewSet):
    queryset = EnvioFormulacion.objects.all()
    serializer_class = EnvioFormulacionSerializer
    filterset_fields = ['unidad', 'gestion', 'activo']

    @action(detail=True, methods=['post'])
    def devolver(self, request, pk=None):
        envio = self.get_object()

        error = _verificar_transicion(request.user, envio, 'observar')
        if error:
            return Response(
                {'error': error['mensaje']},
                status=status.HTTP_403_FORBIDDEN,
            )

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

        if obs.estado not in ('abierta', 'respondida'):
            return Response(
                {'error': f'No se puede subsanar una observación en estado "{obs.get_estado_display()}"'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        respuesta = request.data.get('respuesta', '')
        if not respuesta.strip():
            return Response(
                {'error': 'La respuesta es obligatoria para subsanar una observación'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        obs.respuesta = respuesta
        obs.evidencia_subsanacion = request.data.get('evidencia', '')
        obs.estado = 'aceptada'
        obs.save()
        return Response(ObservacionSerializer(obs).data)


class AprobacionViewSet(viewsets.ModelViewSet):
    queryset = Aprobacion.objects.all()
    serializer_class = AprobacionSerializer
    filterset_fields = ['gestion', 'tipo', 'estado']


class ConsolidacionViewSet(viewsets.ViewSet):

    @action(detail=False, methods=['post'])
    def consolidar(self, request):
        gestion = request.data.get('gestion')
        if not gestion:
            return Response(
                {'error': 'El parámetro "gestion" es requerido'},
                status=status.HTTP_400_BAD_REQUEST
            )

        error = _verificar_transicion(request.user, type('Envio', (), {'estado_anterior': 'enviado'})(), 'aprobar')
        if error:
            return Response(
                {'error': error['mensaje']},
                status=status.HTTP_403_FORBIDDEN,
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
