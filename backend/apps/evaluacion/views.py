from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count

from .models import (
    Evaluacion, CriterioEvaluacion, ResultadoEvaluacion,
    LeccionAprendida, Recomendacion,
)
from .serializers import (
    EvaluacionSerializer, EvaluacionListSerializer,
    CriterioEvaluacionSerializer, ResultadoEvaluacionSerializer,
    LeccionAprendidaSerializer, RecomendacionSerializer,
)
from .services import generar_evaluacion, calcular_score_global


class EvaluacionViewSet(viewsets.ModelViewSet):
    queryset = Evaluacion.objects.select_related('plan').annotate(
        total_criterios=Count('criterios'),
        total_resultados=Count('resultados'),
    )
    filterset_fields = ['plan', 'fiscal_year', 'evaluation_type', 'status', 'period']
    search_fields = ['conclusions', 'recommendations', 'responsible_team']
    ordering_fields = ['fiscal_year', 'evaluation_type', 'created_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return EvaluacionListSerializer
        return EvaluacionSerializer

    @action(detail=True, methods=['get'])
    def resultados(self, request, pk=None):
        """GET /api/v1/evaluaciones/{id}/resultados/

        Retorna los resultados evaluados con desglose por POAU, unidad y PAD.
        """
        evaluacion = self.get_object()
        resultados = ResultadoEvaluacion.objects.filter(
            evaluacion=evaluacion,
        ).select_related('poau', 'unidad', 'resultado_pad')

        poau_results = resultados.filter(poau__isnull=False).values(
            'id', 'poau__codigo', 'poau__nombre', 'score_global', 'status', 'observations',
        )
        unidad_results = resultados.filter(
            poau__isnull=True, unidad__isnull=False, resultado_pad__isnull=True,
        ).values(
            'id', 'unidad__codigo', 'unidad__nombre', 'score_global', 'status', 'observations',
        )
        pad_results = resultados.filter(resultado_pad__isnull=False).values(
            'id', 'resultado_pad__codigo', 'resultado_pad__nombre',
            'score_global', 'status', 'observations',
        )

        criterios = evaluacion.criterios.values(
            'id', 'criterion', 'score', 'weight', 'justification',
        )

        return Response({
            'evaluacion': EvaluacionSerializer(evaluacion).data,
            'criterios': list(criterios),
            'resultados_poau': list(poau_results),
            'resultados_unidad': list(unidad_results),
            'resultados_pad': list(pad_results),
            'resumen': {
                'total': resultados.count(),
                'cumple': resultados.filter(status='cumple').count(),
                'parcial': resultados.filter(status='parcial').count(),
                'no_cumple': resultados.filter(status='no_cumple').count(),
            },
        })

    @action(detail=False, methods=['post'])
    def generar(self, request):
        """POST /api/v1/evaluaciones/generar/

        Auto-genera una evaluación a partir de datos de seguimiento.

        Body:
            gestion (int): año fiscal
            tipo (str): tipo de evaluación (anual, medio_termino, final, especifica)
            plan_id (uuid, opcional): ID del plan a evaluar
            periodo (str, opcional): período (Q1-Q4, S1-S2, AN)
        """
        gestion = request.data.get('gestion')
        tipo = request.data.get('tipo', 'anual')
        plan_id = request.data.get('plan_id')
        periodo = request.data.get('periodo', 'AN')

        if not gestion:
            return Response(
                {'error': 'El campo "gestion" es requerido'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if tipo not in dict(Evaluacion.TIPO_EVALUACION_CHOICES):
            return Response(
                {'error': f'Tipo de evaluación no válido: {tipo}'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            evaluacion = generar_evaluacion(
                gestion=int(gestion),
                tipo=tipo,
                plan_id=plan_id,
                periodo=periodo,
            )
            return Response(
                EvaluacionSerializer(evaluacion).data,
                status=status.HTTP_201_CREATED,
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )


class CriterioEvaluacionViewSet(viewsets.ModelViewSet):
    queryset = CriterioEvaluacion.objects.select_related('evaluacion')
    serializer_class = CriterioEvaluacionSerializer
    filterset_fields = ['evaluacion', 'criterion']
    ordering_fields = ['criterion', 'score', 'weight']


class ResultadoEvaluacionViewSet(viewsets.ModelViewSet):
    queryset = ResultadoEvaluacion.objects.select_related(
        'evaluacion', 'poau', 'unidad', 'resultado_pad',
    )
    serializer_class = ResultadoEvaluacionSerializer
    filterset_fields = ['evaluacion', 'status', 'poau', 'unidad', 'resultado_pad']
    ordering_fields = ['score_global', 'status']


class LeccionAprendidaViewSet(viewsets.ModelViewSet):
    queryset = LeccionAprendida.objects.select_related('evaluacion')
    serializer_class = LeccionAprendidaSerializer
    filterset_fields = ['evaluacion', 'category']
    search_fields = ['title', 'description']
    ordering_fields = ['category', 'title']


class RecomendacionViewSet(viewsets.ModelViewSet):
    queryset = Recomendacion.objects.select_related('evaluacion')
    serializer_class = RecomendacionSerializer
    filterset_fields = ['evaluacion', 'priority', 'status']
    search_fields = ['description', 'responsible_unit']
    ordering_fields = ['priority', 'due_date']
