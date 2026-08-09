"""API V2 de evaluación del SIS-PE (WP-08 / /api/v2/sis-pe/evaluaciones/)."""
from rest_framework import viewsets

from apps.accounts.permissions import TieneAlgunaCapacidad
from apps.evaluacion.models import Evaluacion, LeccionAprendida, Recomendacion
from apps.evaluacion.serializers import (
    EvaluacionSerializer,
    LeccionAprendidaSerializer,
    RecomendacionSerializer,
)

CAPACIDADES_ESCRITURA = [
    'sis_pe.pad.edit', 'sis_pe.pei.edit', 'sis_pe.approve',
]


class EvaluacionV2ViewSet(viewsets.ModelViewSet):
    queryset = Evaluacion.objects.select_related('plan', 'version_instrumento')
    serializer_class = EvaluacionSerializer
    filterset_fields = ['plan', 'version_instrumento', 'fiscal_year', 'status']

    def get_permissions(self):
        if self.action in ('create', 'update', 'partial_update', 'destroy'):
            return [TieneAlgunaCapacidad(*CAPACIDADES_ESCRITURA)]
        return super().get_permissions()


class LeccionV2ViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = LeccionAprendida.objects.select_related('evaluacion')
    serializer_class = LeccionAprendidaSerializer


class RecomendacionV2ViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Recomendacion.objects.select_related('evaluacion')
    serializer_class = RecomendacionSerializer
