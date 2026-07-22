from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import (
    CodigoNivel, AcuerdoInternacional, Normativa, LineamientoPAD,
    ResultadoPAD, ProductoPAD, ResultadoPEI, ProductoPEI,
    ArticulacionPADPEI, IndicadorCadena, AccionPOA, OperacionPOAU,
    ActividadPOAU, ActividadNormativa, TareaPOAU, TareaNormativa,
    SeguimientoPresupuesto, AsignacionObjetoGasto,
)
from .serializers import (
    CodigoNivelSerializer, AcuerdoInternacionalSerializer, NormativaSerializer,
    LineamientoPADSerializer, ResultadoPADSerializer, ProductoPADSerializer,
    ResultadoPEISerializer, ProductoPEISerializer, ArticulacionPADPEISerializer,
    IndicadorCadenaSerializer, AccionPOASerializer, OperacionPOAUSerializer,
    ActividadPOAUSerializer, ActividadNormativaSerializer, TareaPOAUSerializer,
    TareaNormativaSerializer, SeguimientoPresupuestoSerializer,
    AsignacionObjetoGastoSerializer,
)
from .permissions import ArticulacionPermisos
from .services import registrar_auditoria


ESTADO_ACTIONS_MIXIN = '__estado_actions__'


def _add_estado_actions(cls):
    """Decorator-like helper to add enviar/aprobar/observar actions to a ViewSet."""
    if not hasattr(cls, 'estado_actions_added'):
        cls.estado_actions_added = True

        @action(detail=True, methods=['post'])
        def enviar(self, request, pk=None):
            obj = self.get_object()
            obj.estado = 'ENVIADO'
            obj.save(update_fields=['estado'])
            registrar_auditoria(
                usuario=request.user, accion='enviar',
                entidad=obj.__class__.__name__, entidad_id=obj.id,
                detalle=f'Registro enviado a revisión'
            )
            return Response({'status': 'enviado', 'estado': 'ENVIADO'})

        @action(detail=True, methods=['post'])
        def aprobar(self, request, pk=None):
            obj = self.get_object()
            if obj.estado != 'ENVIADO':
                return Response(
                    {'error': 'Solo se puede aprobar registros en estado ENVIADO'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            obj.estado = 'APROBADO'
            obj.save(update_fields=['estado'])
            registrar_auditoria(
                usuario=request.user, accion='aprobar',
                entidad=obj.__class__.__name__, entidad_id=obj.id,
                detalle=f'Registro aprobado'
            )
            return Response({'status': 'aprobado', 'estado': 'APROBADO'})

        @action(detail=True, methods=['post'])
        def observar(self, request, pk=None):
            comentario = request.data.get('comentario', '').strip()
            if not comentario:
                return Response(
                    {'error': 'Se requiere un comentario para observar'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            obj = self.get_object()
            obj.estado = 'OBSERVADO'
            obj.save(update_fields=['estado'])
            registrar_auditoria(
                usuario=request.user, accion='devolver',
                entidad=obj.__class__.__name__, entidad_id=obj.id,
                detalle=f'Registro observado: {comentario[:200]}'
            )
            return Response({'status': 'observado', 'estado': 'OBSERVADO', 'comentario': comentario})

        cls.enviar = enviar
        cls.aprobar = aprobar
        cls.observar = observar

    return cls


# Mixin concreto para heredar las actions
class EstadoActionsMixin:
    """Mixin que agrega actions enviar/aprobar/observar a ViewSets con estado."""

    @action(detail=True, methods=['post'])
    def enviar(self, request, pk=None):
        obj = self.get_object()
        obj.estado = 'ENVIADO'
        obj.save(update_fields=['estado'])
        registrar_auditoria(
            usuario=request.user, accion='enviar',
            entidad=obj.__class__.__name__, entidad_id=str(obj.id),
            detalle='Registro enviado a revisión'
        )
        return Response({'status': 'enviado', 'estado': 'ENVIADO'})

    @action(detail=True, methods=['post'])
    def aprobar(self, request, pk=None):
        obj = self.get_object()
        if obj.estado != 'ENVIADO':
            return Response(
                {'error': 'Solo se puede aprobar registros en estado ENVIADO'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        obj.estado = 'APROBADO'
        obj.save(update_fields=['estado'])
        registrar_auditoria(
            usuario=request.user, accion='aprobar',
            entidad=obj.__class__.__name__, entidad_id=str(obj.id),
            detalle='Registro aprobado'
        )
        return Response({'status': 'aprobado', 'estado': 'APROBADO'})

    @action(detail=True, methods=['post'])
    def observar(self, request, pk=None):
        comentario = request.data.get('comentario', '').strip()
        if not comentario:
            return Response(
                {'error': 'Se requiere un comentario para observar'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        obj = self.get_object()
        obj.estado = 'OBSERVADO'
        obj.save(update_fields=['estado'])
        registrar_auditoria(
            usuario=request.user, accion='devolver',
            entidad=obj.__class__.__name__, entidad_id=str(obj.id),
            detalle=f'Registro observado: {comentario[:200]}'
        )
        return Response({'status': 'observado', 'estado': 'OBSERVADO', 'comentario': comentario})


class CodigoNivelViewSet(viewsets.ModelViewSet):
    queryset = CodigoNivel.objects.all()
    serializer_class = CodigoNivelSerializer
    permission_classes = [ArticulacionPermisos]
    filterset_fields = ['nivel', 'codigo_nivel', 'editable', 'vigencia']
    search_fields = ['nivel', 'ejemplo']
    ordering_fields = ['codigo_nivel', 'nivel']


class AcuerdoInternacionalViewSet(viewsets.ModelViewSet):
    queryset = AcuerdoInternacional.objects.all()
    serializer_class = AcuerdoInternacionalSerializer
    permission_classes = [ArticulacionPermisos]
    filterset_fields = ['tipo_acuerdo', 'activo', 'es_codigo_oficial']
    search_fields = ['codigo', 'denominacion']
    ordering_fields = ['tipo_acuerdo', 'codigo']


class NormativaViewSet(viewsets.ModelViewSet):
    queryset = Normativa.objects.all()
    serializer_class = NormativaSerializer
    permission_classes = [ArticulacionPermisos]
    filterset_fields = ['nivel', 'tipo_norma', 'estado', 'vigencia']
    search_fields = ['codigo_norma', 'denominacion', 'numero_identificador']
    ordering_fields = ['codigo_norma', 'fecha_emision']


class LineamientoPADViewSet(viewsets.ModelViewSet):
    queryset = LineamientoPAD.objects.all()
    serializer_class = LineamientoPADSerializer
    permission_classes = [ArticulacionPermisos]
    filterset_fields = ['activo', 'gestion_desde', 'gestion_hasta']
    search_fields = ['codigo', 'denominacion']
    ordering_fields = ['codigo']


class ResultadoPADViewSet(EstadoActionsMixin, viewsets.ModelViewSet):
    queryset = ResultadoPAD.objects.all()
    serializer_class = ResultadoPADSerializer
    permission_classes = [ArticulacionPermisos]
    filterset_fields = ['vigencia_desde', 'vigencia_hasta', 'estado', 'lineamiento_pad']
    search_fields = ['codigo_resultado', 'denominacion']
    ordering_fields = ['codigo_resultado', 'vigencia_desde']


class ProductoPADViewSet(viewsets.ModelViewSet):
    queryset = ProductoPAD.objects.all()
    serializer_class = ProductoPADSerializer
    permission_classes = [ArticulacionPermisos]
    filterset_fields = ['resultado_pad']
    search_fields = ['codigo_producto', 'denominacion']
    ordering_fields = ['codigo_producto']


class ResultadoPEIViewSet(viewsets.ModelViewSet):
    queryset = ResultadoPEI.objects.all()
    serializer_class = ResultadoPEISerializer
    permission_classes = [ArticulacionPermisos]
    filterset_fields = ['vigencia_desde', 'vigencia_hasta', 'cod_entidad']
    search_fields = ['codigo_resultado', 'denominacion']
    ordering_fields = ['codigo_resultado', 'vigencia_desde']


class ProductoPEIViewSet(viewsets.ModelViewSet):
    queryset = ProductoPEI.objects.all()
    serializer_class = ProductoPEISerializer
    permission_classes = [ArticulacionPermisos]
    filterset_fields = ['resultado_pei']
    search_fields = ['codigo_producto', 'denominacion']
    ordering_fields = ['codigo_producto']


class ArticulacionPADPEIViewSet(EstadoActionsMixin, viewsets.ModelViewSet):
    queryset = ArticulacionPADPEI.objects.all()
    serializer_class = ArticulacionPADPEISerializer
    permission_classes = [ArticulacionPermisos]
    filterset_fields = ['producto_pad', 'producto_pei', 'estado', 'tipo_contribucion']
    search_fields = ['justificacion']
    ordering_fields = ['producto_pad', 'producto_pei']


class IndicadorCadenaViewSet(viewsets.ModelViewSet):
    queryset = IndicadorCadena.objects.all()
    serializer_class = IndicadorCadenaSerializer
    permission_classes = [ArticulacionPermisos]
    filterset_fields = ['nivel_indicador', 'producto_pad', 'producto_pei']
    search_fields = ['indicador', 'unidad_medida']
    ordering_fields = ['nivel_indicador', 'indicador']


class AccionPOAViewSet(EstadoActionsMixin, viewsets.ModelViewSet):
    queryset = AccionPOA.objects.all()
    serializer_class = AccionPOASerializer
    permission_classes = [ArticulacionPermisos]
    filterset_fields = ['gestion', 'estado', 'producto_pei', 'unidad_responsable']
    search_fields = ['codigo_accion', 'denominacion', 'programa']
    ordering_fields = ['codigo_accion', 'gestion', 'denominacion']


class OperacionPOAUViewSet(EstadoActionsMixin, viewsets.ModelViewSet):
    queryset = OperacionPOAU.objects.all()
    serializer_class = OperacionPOAUSerializer
    permission_classes = [ArticulacionPermisos]
    filterset_fields = ['accion_poa', 'tipo_operacion', 'estado']
    search_fields = ['codigo_operacion', 'denominacion']
    ordering_fields = ['codigo_operacion', 'denominacion']


class ActividadPOAUViewSet(EstadoActionsMixin, viewsets.ModelViewSet):
    queryset = ActividadPOAU.objects.all()
    serializer_class = ActividadPOAUSerializer
    permission_classes = [ArticulacionPermisos]
    filterset_fields = ['operacion', 'estado']
    search_fields = ['codigo_actividad', 'denominacion']
    ordering_fields = ['codigo_actividad', 'denominacion']


class ActividadNormativaViewSet(viewsets.ModelViewSet):
    queryset = ActividadNormativa.objects.all()
    serializer_class = ActividadNormativaSerializer
    permission_classes = [ArticulacionPermisos]
    filterset_fields = ['actividad', 'normativa', 'obligatorio']
    ordering_fields = ['actividad', 'normativa']


class TareaPOAUViewSet(EstadoActionsMixin, viewsets.ModelViewSet):
    queryset = TareaPOAU.objects.all()
    serializer_class = TareaPOAUSerializer
    permission_classes = [ArticulacionPermisos]
    filterset_fields = ['actividad', 'estado']
    search_fields = ['codigo_tarea', 'denominacion']
    ordering_fields = ['codigo_tarea', 'denominacion']


class TareaNormativaViewSet(viewsets.ModelViewSet):
    queryset = TareaNormativa.objects.all()
    serializer_class = TareaNormativaSerializer
    permission_classes = [ArticulacionPermisos]
    filterset_fields = ['tarea', 'normativa', 'obligatorio']
    ordering_fields = ['tarea', 'normativa']


class SeguimientoPresupuestoViewSet(EstadoActionsMixin, viewsets.ModelViewSet):
    queryset = SeguimientoPresupuesto.objects.all()
    serializer_class = SeguimientoPresupuestoSerializer
    permission_classes = [ArticulacionPermisos]
    filterset_fields = ['gestion', 'estado', 'accion_poa', 'operacion', 'actividad']
    search_fields = ['id_cadena', 'programa']
    ordering_fields = ['gestion', 'id_cadena']


class AsignacionObjetoGastoViewSet(EstadoActionsMixin, viewsets.ModelViewSet):
    queryset = AsignacionObjetoGasto.objects.all()
    serializer_class = AsignacionObjetoGastoSerializer
    permission_classes = [ArticulacionPermisos]
    filterset_fields = ['gestion', 'estado', 'accion_poa', 'operacion', 'actividad', 'tipo_gasto']
    search_fields = ['codigo_asignacion', 'descripcion_objeto']
    ordering_fields = ['codigo_asignacion', 'gestion']
