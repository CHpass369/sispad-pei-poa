from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import (
    ReporteSeguimiento, EntradaSeguimiento, Alerta, UmbralConfiguracion,
)
from .serializers import (
    ReporteSeguimientoSerializer,
    EntradaSeguimientoSerializer,
    EntradaSeguimientoListSerializer,
    AlertaSerializer,
    UmbralConfiguracionSerializer,
)
from .services import (
    determinar_semaforo, dashboard_seguimiento, generar_alertas,
)


class ReporteSeguimientoViewSet(viewsets.ModelViewSet):
    queryset = ReporteSeguimiento.objects.select_related(
        'unidad_organizacional', 'submitted_by', 'approved_by',
    ).all()
    serializer_class = ReporteSeguimientoSerializer
    filterset_fields = ['gestion', 'periodo', 'estado', 'unidad_organizacional']
    search_fields = ['periodo', 'unidad_organizacional__nombre']
    ordering_fields = ['gestion', 'periodo', 'estado', 'created_at']

    @action(detail=True, methods=['post'])
    def enviar(self, request, pk=None):
        """Envia el reporte para validacion."""
        reporte = self.get_object()
        if reporte.estado != 'borrador':
            return Response(
                {'error': 'Solo se pueden enviar reportes en borrador'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        reporte.estado = 'enviado'
        reporte.submitted_at = timezone.now()
        reporte.submitted_by = request.user
        reporte.save()
        serializer = self.get_serializer(reporte)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def validar(self, request, pk=None):
        """Valida el reporte enviado."""
        reporte = self.get_object()
        if reporte.estado != 'enviado':
            return Response(
                {'error': 'Solo se pueden validar reportes enviados'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        reporte.estado = 'validado'
        reporte.save()
        serializer = self.get_serializer(reporte)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def aprobar(self, request, pk=None):
        """Aprueba el reporte validado."""
        reporte = self.get_object()
        if reporte.estado != 'validado':
            return Response(
                {'error': 'Solo se pueden aprobar reportes validados'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        reporte.estado = 'aprobado'
        reporte.approved_at = timezone.now()
        reporte.approved_by = request.user
        reporte.save()
        serializer = self.get_serializer(reporte)
        return Response(serializer.data)


class EntradaSeguimientoViewSet(viewsets.ModelViewSet):
    queryset = EntradaSeguimiento.objects.select_related(
        'actividad', 'reporte', 'reporte__unidad_organizacional'
    ).all()
    serializer_class = EntradaSeguimientoSerializer
    filterset_fields = [
        'reporte', 'reporte__gestion', 'reporte__periodo',
        'actividad', 'actividad__poau__unidad',
    ]
    search_fields = [
        'actividad__codigo', 'actividad__nombre',
        'causa_desviacion', 'evidencia',
    ]
    ordering_fields = [
        'porcentaje_avance_fisico', 'porcentaje_avance_financiero',
        'created_at',
    ]

    def get_queryset(self):
        return EntradaSeguimiento.objects.select_related(
            'reporte', 'actividad', 'actividad__poau',
        ).all()

    def get_serializer_class(self):
        if self.action == 'list':
            return EntradaSeguimientoListSerializer
        return EntradaSeguimientoSerializer

    @action(detail=False, methods=['get'])
    def semaforo(self, request):
        """Retorna estado del semaforo por gestion y periodo."""
        gestion = request.query_params.get('gestion')
        periodo = request.query_params.get('periodo')

        if not gestion:
            return Response(
                {'error': 'gestion es requerido'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        qs = self.get_queryset().filter(
            reporte__gestion=int(gestion)
        )
        if periodo:
            qs = qs.filter(reporte__periodo=periodo)

        resultado = {'verde': [], 'amarillo': [], 'rojo': []}
        for entry in qs:
            semaforo = determinar_semaforo(entry.porcentaje_avance_fisico)
            data = {
                'id': str(entry.id),
                'actividad_codigo': entry.actividad.codigo,
                'actividad_nombre': entry.actividad.nombre,
                'avance_fisico': float(entry.porcentaje_avance_fisico),
                'avance_financiero': float(entry.porcentaje_avance_financiero),
            }
            resultado[semaforo].append(data)

        return Response({
            'gestion': int(gestion),
            'periodo': periodo,
            'resumen': {
                'verde': len(resultado['verde']),
                'amarillo': len(resultado['amarillo']),
                'rojo': len(resultado['rojo']),
                'total': (
                    len(resultado['verde'])
                    + len(resultado['amarillo'])
                    + len(resultado['rojo'])
                ),
            },
            'detalle': resultado,
        })

    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        """Retorna datos agregados del dashboard de seguimiento."""
        gestion = request.query_params.get('gestion')
        if not gestion:
            return Response(
                {'error': 'gestion es requerido'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        data = dashboard_seguimiento(int(gestion))
        return Response(data)


class AlertaViewSet(viewsets.ModelViewSet):
    queryset = Alerta.objects.select_related(
        'entrada', 'entrada__actividad',
        'resuelta_por',
    ).all()
    serializer_class = AlertaSerializer
    filterset_fields = ['tipo', 'severidad', 'activa', 'entrada']
    search_fields = ['mensaje', 'entrada__actividad__nombre']
    ordering_fields = ['created_at', 'severidad', 'tipo']

    @action(detail=False, methods=['get'])
    def activas(self, request):
        """Retorna todas las alertas activas sin resolver."""
        alertas = self.get_queryset().filter(activa=True)
        page = self.paginate_queryset(alertas)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(alertas, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def resolver(self, request, pk=None):
        """Marca una alerta como resuelta."""
        alerta = self.get_object()
        if not alerta.activa:
            return Response(
                {'error': 'La alerta ya esta resuelta'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        alerta.activa = False
        alerta.resuelta_en = timezone.now()
        alerta.resuelta_por = request.user
        alerta.save()
        serializer = self.get_serializer(alerta)
        return Response(serializer.data)


class UmbralConfiguracionViewSet(viewsets.ModelViewSet):
    queryset = UmbralConfiguracion.objects.all()
    serializer_class = UmbralConfiguracionSerializer
    filterset_fields = ['activo', 'tipo_umbral']
    search_fields = ['tipo_umbral', 'descripcion']
    ordering_fields = ['tipo_umbral', 'porcentaje_minimo']
