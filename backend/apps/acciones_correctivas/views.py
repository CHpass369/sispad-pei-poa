from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count, Q
from django.utils import timezone

from .models import AccionCorrectiva, CompromisoAccionCorrectiva
from .serializers import (
    AccionCorrectivaSerializer, AccionCorrectivaListSerializer,
    CompromisoAccionCorrectivaSerializer, CompromisoAccionCorrectivaListSerializer,
)
from .services import verificar_vencimiento, obtener_acciones_por_cumplir


class AccionCorrectivaViewSet(viewsets.ModelViewSet):
    queryset = AccionCorrectiva.objects.select_related(
        'alerta', 'entry', 'responsible', 'responsible_unit', 'verified_by',
    ).annotate(
        total_compromisos=Count('compromisos'),
        compromisos_cumplidos=Count(
            'compromisos', filter=Q(compromisos__status='cumplido'),
        ),
    )
    filterset_fields = [
        'status', 'gestion', 'responsible', 'responsible_unit',
        'alerta', 'entry',
    ]
    search_fields = ['description', 'cause', 'expected_result', 'evidence']
    ordering_fields = [
        'start_date', 'due_date', 'status', 'gestion', 'created_at',
    ]

    def get_serializer_class(self):
        if self.action == 'list':
            return AccionCorrectivaListSerializer
        return AccionCorrectivaSerializer

    @action(detail=True, methods=['post'])
    def verificar(self, request, pk=None):
        accion = self.get_object()
        accion.verified_by = request.user
        accion.verified_at = timezone.now()
        accion.save(update_fields=['verified_by', 'verified_at', 'updated_at'])
        return Response({
            'id': str(accion.id),
            'verified_by': request.user.email,
            'verified_at': accion.verified_at,
            'status': accion.status,
        })

    @action(detail=False, methods=['get'])
    def vencidas(self, request):
        resultados = verificar_vencimiento()
        return Response({
            'total': len(resultados),
            'acciones': resultados,
        })

    @action(detail=False, methods=['get'])
    def por_cumplir(self, request):
        dias = int(request.query_params.get('dias', 7))
        resultados = obtener_acciones_por_cumplir(dias=dias)
        return Response({
            'dias': dias,
            'total': len(resultados),
            'acciones': resultados,
        })


class CompromisoAccionCorrectivaViewSet(viewsets.ModelViewSet):
    queryset = CompromisoAccionCorrectiva.objects.select_related(
        'accion_correctiva',
    )
    filterset_fields = ['accion_correctiva', 'status']
    search_fields = ['description', 'notes']
    ordering_fields = ['due_date', 'status', 'completed_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return CompromisoAccionCorrectivaListSerializer
        return CompromisoAccionCorrectivaSerializer

    def perform_update(self, serializer):
        instance = serializer.save()
        if instance.status == 'cumplido' and not instance.completed_at:
            instance.completed_at = timezone.now()
            instance.save(update_fields=['completed_at', 'updated_at'])
