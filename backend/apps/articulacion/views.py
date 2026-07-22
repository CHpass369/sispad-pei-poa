from rest_framework import viewsets
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


class CodigoNivelViewSet(viewsets.ModelViewSet):
    queryset = CodigoNivel.objects.all()
    serializer_class = CodigoNivelSerializer
    filterset_fields = ['nivel', 'codigo_nivel', 'editable', 'vigencia']
    search_fields = ['nivel', 'ejemplo']
    ordering_fields = ['codigo_nivel', 'nivel']


class AcuerdoInternacionalViewSet(viewsets.ModelViewSet):
    queryset = AcuerdoInternacional.objects.all()
    serializer_class = AcuerdoInternacionalSerializer
    filterset_fields = ['tipo_acuerdo', 'activo', 'es_codigo_oficial']
    search_fields = ['codigo', 'denominacion']
    ordering_fields = ['tipo_acuerdo', 'codigo']


class NormativaViewSet(viewsets.ModelViewSet):
    queryset = Normativa.objects.all()
    serializer_class = NormativaSerializer
    filterset_fields = ['nivel', 'tipo_norma', 'estado', 'vigencia']
    search_fields = ['codigo_norma', 'denominacion', 'numero_identificador']
    ordering_fields = ['codigo_norma', 'fecha_emision']


class LineamientoPADViewSet(viewsets.ModelViewSet):
    queryset = LineamientoPAD.objects.all()
    serializer_class = LineamientoPADSerializer
    filterset_fields = ['activo', 'gestion_desde', 'gestion_hasta']
    search_fields = ['codigo', 'denominacion']
    ordering_fields = ['codigo']


class ResultadoPADViewSet(viewsets.ModelViewSet):
    queryset = ResultadoPAD.objects.all()
    serializer_class = ResultadoPADSerializer
    filterset_fields = ['vigencia_desde', 'vigencia_hasta', 'estado', 'lineamiento_pad']
    search_fields = ['codigo_resultado', 'denominacion']
    ordering_fields = ['codigo_resultado', 'vigencia_desde']


class ProductoPADViewSet(viewsets.ModelViewSet):
    queryset = ProductoPAD.objects.all()
    serializer_class = ProductoPADSerializer
    filterset_fields = ['resultado_pad']
    search_fields = ['codigo_producto', 'denominacion']
    ordering_fields = ['codigo_producto']


class ResultadoPEIViewSet(viewsets.ModelViewSet):
    queryset = ResultadoPEI.objects.all()
    serializer_class = ResultadoPEISerializer
    filterset_fields = ['vigencia_desde', 'vigencia_hasta', 'cod_entidad']
    search_fields = ['codigo_resultado', 'denominacion']
    ordering_fields = ['codigo_resultado', 'vigencia_desde']


class ProductoPEIViewSet(viewsets.ModelViewSet):
    queryset = ProductoPEI.objects.all()
    serializer_class = ProductoPEISerializer
    filterset_fields = ['resultado_pei']
    search_fields = ['codigo_producto', 'denominacion']
    ordering_fields = ['codigo_producto']


class ArticulacionPADPEIViewSet(viewsets.ModelViewSet):
    queryset = ArticulacionPADPEI.objects.all()
    serializer_class = ArticulacionPADPEISerializer
    filterset_fields = ['producto_pad', 'producto_pei', 'estado', 'tipo_contribucion']
    search_fields = ['justificacion']
    ordering_fields = ['producto_pad', 'producto_pei']


class IndicadorCadenaViewSet(viewsets.ModelViewSet):
    queryset = IndicadorCadena.objects.all()
    serializer_class = IndicadorCadenaSerializer
    filterset_fields = ['nivel_indicador', 'producto_pad', 'producto_pei']
    search_fields = ['indicador', 'unidad_medida']
    ordering_fields = ['nivel_indicador', 'indicador']


class AccionPOAViewSet(viewsets.ModelViewSet):
    queryset = AccionPOA.objects.all()
    serializer_class = AccionPOASerializer
    filterset_fields = ['gestion', 'estado', 'producto_pei', 'unidad_responsable']
    search_fields = ['codigo_accion', 'denominacion', 'programa']
    ordering_fields = ['codigo_accion', 'gestion', 'denominacion']


class OperacionPOAUViewSet(viewsets.ModelViewSet):
    queryset = OperacionPOAU.objects.all()
    serializer_class = OperacionPOAUSerializer
    filterset_fields = ['accion_poa', 'tipo_operacion', 'estado']
    search_fields = ['codigo_operacion', 'denominacion']
    ordering_fields = ['codigo_operacion', 'denominacion']


class ActividadPOAUViewSet(viewsets.ModelViewSet):
    queryset = ActividadPOAU.objects.all()
    serializer_class = ActividadPOAUSerializer
    filterset_fields = ['operacion', 'estado']
    search_fields = ['codigo_actividad', 'denominacion']
    ordering_fields = ['codigo_actividad', 'denominacion']


class ActividadNormativaViewSet(viewsets.ModelViewSet):
    queryset = ActividadNormativa.objects.all()
    serializer_class = ActividadNormativaSerializer
    filterset_fields = ['actividad', 'normativa', 'obligatorio']
    ordering_fields = ['actividad', 'normativa']


class TareaPOAUViewSet(viewsets.ModelViewSet):
    queryset = TareaPOAU.objects.all()
    serializer_class = TareaPOAUSerializer
    filterset_fields = ['actividad', 'estado']
    search_fields = ['codigo_tarea', 'denominacion']
    ordering_fields = ['codigo_tarea', 'denominacion']


class TareaNormativaViewSet(viewsets.ModelViewSet):
    queryset = TareaNormativa.objects.all()
    serializer_class = TareaNormativaSerializer
    filterset_fields = ['tarea', 'normativa', 'obligatorio']
    ordering_fields = ['tarea', 'normativa']


class SeguimientoPresupuestoViewSet(viewsets.ModelViewSet):
    queryset = SeguimientoPresupuesto.objects.all()
    serializer_class = SeguimientoPresupuestoSerializer
    filterset_fields = ['gestion', 'estado', 'accion_poa', 'operacion', 'actividad']
    search_fields = ['id_cadena', 'programa']
    ordering_fields = ['gestion', 'id_cadena']


class AsignacionObjetoGastoViewSet(viewsets.ModelViewSet):
    queryset = AsignacionObjetoGasto.objects.all()
    serializer_class = AsignacionObjetoGastoSerializer
    filterset_fields = ['gestion', 'estado', 'accion_poa', 'operacion', 'actividad', 'tipo_gasto']
    search_fields = ['codigo_asignacion', 'descripcion_objeto']
    ordering_fields = ['codigo_asignacion', 'gestion']
