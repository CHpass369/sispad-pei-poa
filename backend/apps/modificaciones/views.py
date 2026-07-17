from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from .models import SolicitudModificacion, CambioModificacion, ImpactoModificacion
from .serializers import (
    SolicitudModificacionSerializer,
    SolicitudModificacionListSerializer,
    CambioModificacionSerializer,
    ImpactoModificacionSerializer,
)
from .services import aplicar_modificacion, calcular_impacto_financiero, verificar_compatibilidad


class SolicitudModificacionViewSet(viewsets.ModelViewSet):
    queryset = SolicitudModificacion.objects.select_related(
        'solicitado_por', 'poau',
    ).prefetch_related('cambios', 'impacto').all()
    filterset_fields = ['tipo', 'gestion_fiscal', 'estado', 'entidad_afectada_tipo', 'poau']
    search_fields = ['motivo', 'informe_tecnico', 'documento_legal', 'entidad_afectada_tipo']
    ordering_fields = ['gestion_fiscal', 'tipo', 'estado', 'created_at', 'fecha_efectiva']

    def get_serializer_class(self):
        if self.action == 'list':
            return SolicitudModificacionListSerializer
        return SolicitudModificacionSerializer

    @action(detail=True, methods=['post'])
    def aprobar(self, request, pk=None):
        solicitud = self.get_object()
        if solicitud.estado not in ('en_revision', 'borrador'):
            return Response(
                {'error': f'No se puede aprobar una solicitud en estado "{solicitud.get_estado_display()}"'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        compatibilidad = verificar_compatibilidad(solicitud)
        if not compatibilidad['compatible']:
            return Response(
                {'error': 'La solicitud no es compatible con el estado actual de la entidad.',
                 'detalles': compatibilidad['detalles']},
                status=status.HTTP_400_BAD_REQUEST,
            )

        solicitud.estado = 'aprobada'
        solicitud.observaciones = request.data.get('observaciones', solicitud.observaciones)
        solicitud.save(update_fields=['estado', 'observaciones', 'updated_at'])

        calcular_impacto_financiero(solicitud)

        resultado = aplicar_modificacion(solicitud)

        return Response({
            'mensaje': 'Solicitud aprobada y aplicada correctamente.',
            'resultado': resultado,
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def rechazar(self, request, pk=None):
        solicitud = self.get_object()
        if solicitud.estado not in ('en_revision', 'borrador'):
            return Response(
                {'error': f'No se puede rechazar una solicitud en estado "{solicitud.get_estado_display()}"'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        justificacion = request.data.get('justificacion', '')
        if not justificacion:
            return Response(
                {'error': 'Se requiere el campo "justificacion" para rechazar la solicitud'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        solicitud.estado = 'rechazada'
        solicitud.observaciones = justificacion
        solicitud.save(update_fields=['estado', 'observaciones', 'updated_at'])

        return Response({
            'mensaje': 'Solicitud rechazada.',
            'solicitud_id': str(solicitud.id),
            'estado': solicitud.estado,
        }, status=status.HTTP_200_OK)


class CambioModificacionViewSet(viewsets.ModelViewSet):
    queryset = CambioModificacion.objects.select_related('solicitud').all()
    serializer_class = CambioModificacionSerializer
    filterset_fields = ['solicitud', 'campo']
    search_fields = ['campo', 'valor_anterior', 'valor_propuesto']
    ordering_fields = ['campo', 'created_at']


class ImpactoModificacionViewSet(viewsets.ModelViewSet):
    queryset = ImpactoModificacion.objects.select_related('solicitud').all()
    serializer_class = ImpactoModificacionSerializer
    filterset_fields = ['solicitud']
    ordering_fields = ['impacto_financiero', 'created_at']
