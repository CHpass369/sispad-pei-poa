from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction
from django.utils import timezone
from django.shortcuts import get_object_or_404
from .models import (
    Plan, NodoPlanificacion, AccionMedianoPlazo, AccionCortoPlazo,
    ArticulacionPlanificacion, PlanVersion
)
from .serializers import (
    PlanSerializer, NodoPlanificacionSerializer,
    AccionMedianoPlazoSerializer, AccionCortoPlazoSerializer,
    ArticulacionPlanificacionSerializer, PlanVersionSerializer,
    MatrizArbolBuilder, NodoArbolSerializer,
)
from apps.indicadores.models import Indicador, MetaProgramada, Operacion
from apps.core.permissions import IsPlanificador


class PlanViewSet(viewsets.ModelViewSet):
    queryset = Plan.objects.all()
    serializer_class = PlanSerializer
    filterset_fields = ['tipo', 'activo']
    search_fields = ['codigo', 'nombre']

    @action(detail=True, methods=['post'])
    def versionar(self, request, pk=None):
        plan = self.get_object()
        data = request.data
        version_name = data.get('version_name', '')
        change_reason = data.get('change_reason', '')
        valid_from = data.get('valid_from')
        valid_to = data.get('valid_to')

        if not version_name or not change_reason:
            return Response(
                {'error': 'version_name y change_reason son requeridos'},
                status=status.HTTP_400_BAD_REQUEST
            )

        last_version = PlanVersion.objects.filter(plan=plan).order_by('-version_number').first()
        next_number = (last_version.version_number + 1) if last_version else 1

        if last_version and last_version.status == 'borrador':
            last_version.status = 'obsoleto'
            last_version.save()

        with transaction.atomic():
            version = PlanVersion.objects.create(
                plan=plan,
                version_number=next_number,
                version_name=version_name,
                status='borrador',
                valid_from=valid_from or timezone.now().date(),
                valid_to=valid_to,
                change_reason=change_reason,
                created_by=request.user,
            )

        return Response(
            PlanVersionSerializer(version).data,
            status=status.HTTP_201_CREATED
        )


class PlanVersionViewSet(viewsets.ModelViewSet):
    queryset = PlanVersion.objects.all()
    serializer_class = PlanVersionSerializer
    filterset_fields = ['plan', 'status']

    @action(detail=True, methods=['post'])
    def aprobar(self, request, pk=None):
        version = self.get_object()
        if version.status != 'borrador':
            return Response(
                {'error': 'Solo las versiones en borrador pueden ser aprobadas'},
                status=status.HTTP_400_BAD_REQUEST
            )
        if version.immutable:
            return Response(
                {'error': 'Esta versión es inmutable y no puede ser modificada'},
                status=status.HTTP_400_BAD_REQUEST
            )

        with transaction.atomic():
            PlanVersion.objects.filter(
                plan=version.plan, status='aprobado'
            ).update(status='obsoleto')

            version.status = 'aprobado'
            version.approved_at = timezone.now()
            version.approved_by = request.user
            version.save()

        return Response(PlanVersionSerializer(version).data)


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


class MatrizCompletaViewSet(viewsets.ViewSet):
    """Complete PGDESA→PDESA→PAD→PEI→POA hierarchy.

    A plan is active for a requested management when the year is inside its
    inclusive ``gestion_inicio``/``gestion_fin`` range.  Versioned nodes and
    planning articulations use an exact ``gestion`` match; PAD and PEI records
    use their inclusive ``vigencia_desde``/``vigencia_hasta`` ranges; POA
    actions use an exact ``gestion`` match.
    """

    permission_classes = [IsPlanificador]

    def list(self, request):
        gestion_value = request.query_params.get('gestion')
        nivel = request.query_params.get('nivel')
        padre_id = request.query_params.get('padre_id')

        if not gestion_value:
            return Response({'error': 'gestión requerida'}, status=400)
        try:
            gestion = int(gestion_value)
        except (TypeError, ValueError):
            return Response({'error': 'gestión inválida'}, status=400)

        queryset = NodoPlanificacion.objects.filter(
            gestion=gestion,
            activo=True,
            plan__activo=True,
            plan__gestion_inicio__lte=gestion,
            plan__gestion_fin__gte=gestion,
            plan__tipo__in=('pgdesa', 'pdesa'),
        ).select_related('plan', 'padre')
        all_nodes = list(queryset.order_by('plan__tipo', 'nivel', 'codigo'))

        if padre_id:
            try:
                padre = next(
                    node.id for node in all_nodes if str(node.id) == str(padre_id)
                )
            except StopIteration:
                padre = None
            if padre is None:
                return Response({'data': [], 'stats': {'total': 0}})
            queryset_nodes = [node for node in all_nodes if node.padre_id == padre]
        elif nivel:
            queryset_nodes = [
                node for node in all_nodes
                if node.nivel == nivel and node.padre_id is None
            ]
        else:
            queryset_nodes = [
                node for node in all_nodes
                if node.plan.tipo == 'pgdesa'
                and node.nivel == 'eje'
                and node.padre_id is None
            ]

        queryset_nodes.sort(key=lambda node: (node.codigo, str(node.id)))
        lazy = nivel == 'eje' and not padre_id
        builder = MatrizArbolBuilder(all_nodes, gestion, request=request)
        serializer = NodoArbolSerializer(
            queryset_nodes,
            many=True,
            context={'gestion': gestion, 'matriz_builder': builder, 'matriz_lazy': lazy},
        )
        por_nivel = {}
        for node in all_nodes:
            por_nivel[node.nivel] = por_nivel.get(node.nivel, 0) + 1
        stats = {'total': len(queryset_nodes)}
        if queryset_nodes:
            stats['por_nivel'] = por_nivel
        return Response({
            'data': serializer.data,
            'stats': stats,
        })
