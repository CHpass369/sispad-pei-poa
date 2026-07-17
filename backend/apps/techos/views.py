from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import TechoPresupuestario, DistribucionTecho, MovimientoTecho
from .serializers import (
    TechoPresupuestarioSerializer, DistribucionTechoSerializer,
    MovimientoTechoSerializer
)
from .services import validar_movimiento, aplicar_movimiento, obtener_saldo_disponible


class TechoPresupuestarioViewSet(viewsets.ModelViewSet):
    queryset = TechoPresupuestario.objects.all()
    serializer_class = TechoPresupuestarioSerializer
    filterset_fields = ['gestion', 'fuente', 'activo']


class DistribucionTechoViewSet(viewsets.ModelViewSet):
    queryset = DistribucionTecho.objects.all()
    serializer_class = DistribucionTechoSerializer
    filterset_fields = ['techo', 'da', 'ue', 'unidad', 'programa', 'activo']


class MovimientoTechoViewSet(viewsets.ModelViewSet):
    queryset = MovimientoTecho.objects.all()
    serializer_class = MovimientoTechoSerializer
    filterset_fields = ['techo', 'movement_type', 'approved_by']

    @action(detail=True, methods=['post'])
    def mover(self, request, pk=None):
        movimiento = self.get_object()

        errores = validar_movimiento(movimiento)
        if errores:
            return Response(
                {'error': 'Validación del movimiento fallida',
                 'detalles': errores},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            aplicar_movimiento(movimiento)
            return Response({
                'status': 'ok',
                'mensaje': 'Movimiento aplicado correctamente',
                'saldo_disponible': str(obtener_saldo_disponible(movimiento.techo)),
            })
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['get'])
    def saldo(self, request):
        techo_id = request.query_params.get('techo')
        if not techo_id:
            return Response(
                {'error': 'El parámetro techo es requerido'},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            techo = TechoPresupuestario.objects.get(pk=techo_id)
        except TechoPresupuestario.DoesNotExist:
            return Response(
                {'error': 'Techo no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
        return Response({
            'techo_id': str(techo.id),
            'monto_total': str(techo.monto_total),
            'saldo_disponible': str(obtener_saldo_disponible(techo)),
        })
