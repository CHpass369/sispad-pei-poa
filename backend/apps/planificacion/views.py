from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction
from .models import Plan, NodoPlanificacion, AccionMedianoPlazo, AccionCortoPlazo, ArticulacionPlanificacion
from .serializers import (
    PlanSerializer, NodoPlanificacionSerializer,
    AccionMedianoPlazoSerializer, AccionCortoPlazoSerializer,
    ArticulacionPlanificacionSerializer
)
from apps.indicadores.models import Indicador, MetaProgramada, Operacion


class PlanViewSet(viewsets.ModelViewSet):
    queryset = Plan.objects.all()
    serializer_class = PlanSerializer
    filterset_fields = ['tipo', 'activo']
    search_fields = ['codigo', 'nombre']


class NodoPlanificacionViewSet(viewsets.ModelViewSet):
    queryset = NodoPlanificacion.objects.all()
    serializer_class = NodoPlanificacionSerializer
    filterset_fields = ['plan', 'nivel', 'gestion', 'activo', 'padre']
    search_fields = ['codigo', 'nombre']


class AccionMedianoPlazoViewSet(viewsets.ModelViewSet):
    queryset = AccionMedianoPlazo.objects.all()
    serializer_class = AccionMedianoPlazoSerializer
    search_fields = ['codigo', 'nombre']


class AccionCortoPlazoViewSet(viewsets.ModelViewSet):
    queryset = AccionCortoPlazo.objects.all()
    serializer_class = AccionCortoPlazoSerializer
    filterset_fields = ['gestion', 'unidad_responsable', 'accion_mediano_plazo']
    search_fields = ['codigo', 'nombre']


class ArticulacionPlanificacionViewSet(viewsets.ModelViewSet):
    queryset = ArticulacionPlanificacion.objects.all()
    serializer_class = ArticulacionPlanificacionSerializer
    filterset_fields = ['gestion', 'es_principal']


class FormulacionViewSet(viewsets.ViewSet):
    """Endpoint para envío de formulación desde el wizard Angular."""

    @action(detail=False, methods=['post'])
    def enviar(self, request):
        """
        POST /api/v1/formulacion/enviar/
        Recibe la formulación completa desde el wizard Angular.
        """
        data = request.data
        gestion = data.get('gestion')
        unidad_id = data.get('unidad_id')
        accion_data = data.get('accion', {})
        producto_data = data.get('producto', {})
        operaciones_data = data.get('operaciones', [])

        if not gestion or not accion_data.get('codigo'):
            return Response(
                {'error': 'gestión y código de acción son requeridos'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            with transaction.atomic():
                # 1. Buscar o crear AccionCortoPlazo
                acp, created = AccionCortoPlazo.objects.get_or_create(
                    codigo=accion_data.get('codigo'),
                    gestion=gestion,
                    defaults={
                        'nombre': accion_data.get('nombre', ''),
                        'justificacion': accion_data.get('justificacion', ''),
                        'fecha_inicio': accion_data.get('fecha_inicio'),
                        'fecha_fin': accion_data.get('fecha_fin'),
                        'unidad_responsable_id': unidad_id,
                    }
                )

                # 2. Crear indicador si viene
                if producto_data.get('indicador_nombre'):
                    ind, _ = Indicador.objects.get_or_create(
                        codigo=f'IND-{accion_data.get("codigo")}',
                        defaults={
                            'nombre': producto_data.get('indicador_nombre'),
                            'formula': producto_data.get('indicador_formula', ''),
                            'linea_base': producto_data.get('linea_base'),
                            'meta_anual': producto_data.get('meta_anual'),
                            'unidad_medida_id': producto_data.get('unidad_medida'),
                        }
                    )
                    MetaProgramada.objects.get_or_create(
                        indicador=ind, gestion=gestion, version=1,
                        defaults={
                            'meta_anual': producto_data.get('meta_anual', 0),
                            'trimestre1': producto_data.get('trimestre1', 0),
                            'trimestre2': producto_data.get('trimestre2', 0),
                            'trimestre3': producto_data.get('trimestre3', 0),
                            'trimestre4': producto_data.get('trimestre4', 0),
                        }
                    )

                # 3. Crear operaciones
                for op_data in operaciones_data:
                    if op_data.get('nombre'):
                        Operacion.objects.create(
                            accion_corto_plazo=acp,
                            codigo=f'OP-{acp.codigo}-{operaciones_data.index(op_data) + 1}',
                            nombre=op_data.get('nombre', ''),
                        )

                return Response({
                    'status': 'ok',
                    'accion_id': str(acp.id),
                    'mensaje': 'Formulación recibida correctamente',
                }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
