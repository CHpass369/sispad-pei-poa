"""API V2 del workflow configurable (WP-08 / /api/v2/platform/workflow/)."""
from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.workflow.models_v2 import (
    WorkflowDefinition,
    WorkflowInstance,
    WorkflowStepDefinition,
    WorkflowTask,
    WorkflowTransition,
)
from apps.workflow.services_v2 import (
    aprobar_workflow,
    avanzar_workflow,
    delegar_tarea,
    iniciar_workflow,
    observar_workflow,
    tarea_actual,
)


class PasoSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowStepDefinition
        fields = ['id', 'orden', 'nombre', 'estado', 'es_inicial', 'es_final']


class TransicionSerializer(serializers.ModelSerializer):
    desde = serializers.CharField(source='desde_paso.nombre', read_only=True, default='(inicio)')
    hacia = serializers.CharField(source='hacia_paso.nombre', read_only=True)

    class Meta:
        model = WorkflowTransition
        fields = ['id', 'nombre', 'desde', 'hacia', 'requiere_aprobacion']


class DefinicionSerializer(serializers.ModelSerializer):
    pasos = PasoSerializer(many=True, read_only=True)
    transiciones = TransicionSerializer(many=True, read_only=True)

    class Meta:
        model = WorkflowDefinition
        fields = [
            'id', 'codigo', 'nombre', 'tipo_entidad', 'descripcion',
            'activo', 'pasos', 'transiciones',
        ]


class InstanciaSerializer(serializers.ModelSerializer):
    definicion_codigo = serializers.CharField(
        source='definicion.codigo', read_only=True,
    )
    tarea_actual = serializers.SerializerMethodField()

    class Meta:
        model = WorkflowInstance
        fields = [
            'id', 'definicion', 'definicion_codigo', 'entidad_tipo',
            'entidad_id', 'estado_actual', 'cerrado', 'iniciado_en',
            'tarea_actual',
        ]
        read_only_fields = [
            'id', 'estado_actual', 'cerrado', 'iniciado_en', 'tarea_actual',
        ]

    def get_tarea_actual(self, obj):
        tarea = tarea_actual(obj)
        if not tarea:
            return None
        return {
            'id': str(tarea.id),
            'paso': tarea.paso.nombre,
            'estado': tarea.estado,
            'asignado_a': (
                tarea.asignado_a.email if tarea.asignado_a else None
            ),
        }


class TareaSerializer(serializers.ModelSerializer):
    paso_nombre = serializers.CharField(source='paso.nombre', read_only=True)
    definicion = serializers.CharField(
        source='instancia.definicion.codigo', read_only=True,
    )

    class Meta:
        model = WorkflowTask
        fields = [
            'id', 'instancia', 'definicion', 'paso_nombre', 'paso',
            'asignado_a', 'estado', 'creado_en', 'completado_en',
        ]


class DefinicionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = WorkflowDefinition.objects.prefetch_related(
        'pasos', 'transiciones__desde_paso', 'transiciones__hacia_paso',
    )
    serializer_class = DefinicionSerializer


class InstanciaViewSet(viewsets.ModelViewSet):
    queryset = WorkflowInstance.objects.select_related(
        'definicion', 'iniciado_por',
    )
    serializer_class = InstanciaSerializer
    filterset_fields = ['definicion', 'entidad_tipo', 'entidad_id', 'cerrado']

    def create(self, request, *args, **kwargs):
        definicion_codigo = request.data.get('definicion')
        entidad_tipo = request.data.get('entidad_tipo')
        entidad_id = request.data.get('entidad_id')
        if not (definicion_codigo and entidad_tipo and entidad_id):
            return Response(
                {'error': 'definicion, entidad_tipo y entidad_id son requeridos'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        instancia, error = iniciar_workflow(
            definicion_codigo, entidad_tipo, entidad_id, request.user,
        )
        if error:
            return Response({'error': error}, status=status.HTTP_400_BAD_REQUEST)
        return Response(
            InstanciaSerializer(instancia).data, status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=['post'])
    def avanzar(self, request, pk=None):
        instancia = self.get_object()
        ok, error = avanzar_workflow(
            instancia, request.user,
            comentario=request.data.get('comentario', ''),
        )
        if not ok:
            return Response({'error': error}, status=status.HTTP_403_FORBIDDEN)
        return Response(InstanciaSerializer(instancia).data)

    @action(detail=True, methods=['post'])
    def aprobar(self, request, pk=None):
        instancia = self.get_object()
        entidad = None
        if instancia.entidad_tipo == 'VersionInstrumento':
            from apps.planificacion.models_v2 import VersionInstrumento
            entidad = VersionInstrumento.objects.filter(
                pk=instancia.entidad_id,
            ).first()
        ok, error = aprobar_workflow(
            instancia, request.user,
            comentario=request.data.get('comentario', ''),
            entidad_destino=entidad,
        )
        if not ok:
            return Response({'error': error}, status=status.HTTP_403_FORBIDDEN)
        return Response(InstanciaSerializer(instancia).data)

    @action(detail=True, methods=['post'])
    def observar(self, request, pk=None):
        instancia = self.get_object()
        texto = request.data.get('texto', '').strip()
        if not texto:
            return Response(
                {'error': 'El texto de la observación es requerido'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        ok, error = observar_workflow(
            instancia, request.user, texto,
            severidad=request.data.get('severidad', 'moderada'),
        )
        if not ok:
            return Response({'error': error}, status=status.HTTP_400_BAD_REQUEST)
        return Response(InstanciaSerializer(instancia).data)

    @action(detail=True, methods=['post'])
    def delegar(self, request, pk=None):
        instancia = self.get_object()
        tarea = tarea_actual(instancia)
        if not tarea:
            return Response(
                {'error': 'No hay tarea en curso'}, status=status.HTTP_400_BAD_REQUEST,
            )
        delegado_a = request.data.get('delegado_a')
        if not delegado_a:
            return Response(
                {'error': 'delegado_a es requerido'}, status=status.HTTP_400_BAD_REQUEST,
            )
        from apps.accounts.models import Usuario
        usuario = Usuario.objects.filter(pk=delegado_a).first()
        if not usuario:
            return Response(
                {'error': 'Usuario no encontrado'}, status=status.HTTP_404_NOT_FOUND,
            )
        delegar_tarea(
            tarea, request.user, usuario,
            motivo=request.data.get('motivo', ''),
        )
        return Response(InstanciaSerializer(instancia).data)


class TareaViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = WorkflowTask.objects.select_related('instancia', 'paso')
    serializer_class = TareaSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.query_params.get('mias') == 'true':
            qs = qs.filter(asignado_a=self.request.user)
        if self.request.query_params.get('instancia'):
            qs = qs.filter(instancia_id=self.request.query_params['instancia'])
        return qs
