from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction
from .models import (
    CodigoNivel, AcuerdoInternacional, MetaAcuerdoInternacional, Normativa, LineamientoPAD,
    ResultadoPAD, ProductoPAD, ResultadoPEI, ProductoPEI,
    ArticulacionPADPEI, IndicadorCadena, AccionPOA, OperacionPOAU,
    ActividadPOAU, ActividadNormativa, TareaPOAU, TareaNormativa,
    SeguimientoPresupuesto, AsignacionObjetoGasto, BorradorMatrizPAD,
)
from .serializers import (
    CodigoNivelSerializer, AcuerdoInternacionalSerializer, MetaAcuerdoInternacionalSerializer, NormativaSerializer,
    LineamientoPADSerializer, ResultadoPADSerializer, ProductoPADSerializer,
    ResultadoPEISerializer, ProductoPEISerializer, ArticulacionPADPEISerializer,
    IndicadorCadenaSerializer, AccionPOASerializer, OperacionPOAUSerializer,
    ActividadPOAUSerializer, ActividadNormativaSerializer, TareaPOAUSerializer,
    TareaNormativaSerializer, SeguimientoPresupuestoSerializer,
    AsignacionObjetoGastoSerializer, BorradorMatrizPADSerializer,
    validar_estructura_resultados,
)
from .permissions import ArticulacionPermisos
from .services import (
    registrar_auditoria,
    materializar_borrador_matriz,
    construir_matriz_a,
    construir_matriz_b,
)


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


class MetaAcuerdoInternacionalViewSet(viewsets.ModelViewSet):
    """Metas de acuerdos internacionales de código largo (NDC/NDT/KMGBF)."""

    queryset = MetaAcuerdoInternacional.objects.all()
    serializer_class = MetaAcuerdoInternacionalSerializer
    permission_classes = [ArticulacionPermisos]
    filterset_fields = ['tipo_acuerdo', 'activo']
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
    filterset_fields = ['nivel_indicador', 'resultado_pad', 'producto_pad', 'producto_pei']
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


class BorradorMatrizPADViewSet(viewsets.ModelViewSet):
    """CRUD del borrador de Matrices PAD (guardado incremental por paso).

    Contrato del PATCH parcial (por sección del wizard):
      ``PATCH /borradores-matriz-pad/{id}/`` con
      ``{"seccion": "resultados", "valores": [...lista completa...]}``
    actualiza únicamente esa sección en ``datos``. Para la colección
    ``resultados`` el PATCH envía la LISTA COMPLETA (el wizard mantiene la
    colección en memoria y la reemplaza al agregar/editar resultado o
    producto). También se acepta ``{"datos": {...}}`` para reemplazar el
    JSON completo de secciones.

    Estructura de la sección ``resultados`` (colección):
      resultados: [
        {denominacion, territorializacion, responsable,
         cuenta_con_financiamiento,
         indicador: {indicador, formula, unidad_medida, linea_base,
                     meta_2030},
         programacion_fisica: {'2026': ...},
         presupuesto_total, presupuesto_anual: {'2026': ...},
         productos: [ {mismos campos que el resultado}, ... ]},
        ...
      ]
    Las secciones legacy p6..p10 (cadena única) siguen siendo aceptadas en
    el PATCH y se transforman a la colección en lectura (retrocompat).

    Actions:
      - ``POST /borradores-matriz-pad/{id}/materializar/``
        Materializa el borrador: por cada resultado de la colección crea
        ResultadoPAD → ProductoPAD → IndicadorCadena en transacción
        atómica; setea ``id_resultado_pad`` y estado=COMPLETO.
      - ``GET /borradores-matriz-pad/{id}/matriz_a/``
        Matriz A (27 columnas) armada server-side. Fuente: modelos
        materializados si ``id_resultado_pad`` existe, si no borrador.datos.
      - ``GET /borradores-matriz-pad/{id}/matriz_b/``
        Matriz B (34 columnas) con el mismo contrato.
    """

    queryset = BorradorMatrizPAD.objects.select_related(
        'id_resultado_pad',
    ).all()
    serializer_class = BorradorMatrizPADSerializer
    permission_classes = [ArticulacionPermisos]
    filterset_fields = ['gestion', 'estado']
    ordering_fields = ['gestion', 'estado', 'created_at']

    def partial_update(self, request, *args, **kwargs):
        """PATCH por sección (guardado incremental) o por datos completo."""
        seccion = request.data.get('seccion')
        if seccion:
            valores = request.data.get('valores')
            if valores is None:
                return Response(
                    {'error': 'Se requiere "valores" junto a "seccion".'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if seccion not in BorradorMatrizPAD.SECCIONES:
                return Response(
                    {'error': f'Sección inválida: {seccion}. '
                              f'Válidas: {", ".join(BorradorMatrizPAD.SECCIONES)}'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if seccion == 'resultados':
                error = validar_estructura_resultados(valores)
                if error:
                    return Response(
                        {'error': error}, status=status.HTTP_400_BAD_REQUEST,
                    )
            instance = self.get_object()
            datos = instance.datos or {}
            datos[seccion] = valores
            instance.datos = datos
            instance.save(update_fields=['datos', 'updated_at'])
            serializer = self.get_serializer(instance)
            return Response(serializer.data)
        return super().partial_update(request, *args, **kwargs)

    @action(detail=True, methods=['post'])
    def materializar(self, request, pk=None):
        """Crea ResultadoPAD → ProductoPAD → IndicadorCadena (atómico).

        La materialización procesa TODA la colección ``resultados``: crea un
        ResultadoPAD por cada resultado y un ProductoPAD por cada producto
        (cada uno con su IndicadorCadena). Devuelve el resumen con conteos.
        """
        borrador = self.get_object()
        try:
            with transaction.atomic():
                creados = materializar_borrador_matriz(
                    borrador, usuario=request.user,
                )
                primer_resultado = creados['resultados'][0]
                borrador.id_resultado_pad = primer_resultado
                borrador.estado = BorradorMatrizPAD.ESTADO_COMPLETO
                borrador.save(
                    update_fields=['id_resultado_pad', 'estado', 'updated_at'],
                )
        except ValueError as exc:
            return Response(
                {'error': str(exc)}, status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as exc:
            registrar_auditoria(
                usuario=request.user, accion='materializar_error',
                entidad='BorradorMatrizPAD', entidad_id=str(borrador.id),
                detalle=f'Error al materializar: {str(exc)[:200]}',
            )
            return Response(
                {'error': f'No se pudo materializar el borrador: {exc}'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        registrar_auditoria(
            usuario=request.user, accion='materializar',
            entidad='BorradorMatrizPAD', entidad_id=str(borrador.id),
            detalle=(
                f'Materializado: {len(creados["resultados"])} resultado(s), '
                f'{len(creados["productos"])} producto(s)'
            ),
        )
        return Response({
            'estado': borrador.estado,
            'id_resultado_pad': str(primer_resultado.id),
            'total_resultados': len(creados['resultados']),
            'total_productos': len(creados['productos']),
            'total_indicadores': len(creados['indicadores']),
            'codigos': {
                'resultados': [r.codigo_resultado for r in creados['resultados']],
                'productos': [p.codigo_producto for p in creados['productos']],
            },
            'ids': {
                'resultados': [str(r.id) for r in creados['resultados']],
                'productos': [str(p.id) for p in creados['productos']],
                'indicadores': [str(i.id) for i in creados['indicadores']],
            },
        })

    @action(detail=True, methods=['get'])
    def matriz_a(self, request, pk=None):
        """Matriz A (27 columnas) — modelos si materializado, borrador si no."""
        borrador = self.get_object()
        return Response(construir_matriz_a(borrador))

    @action(detail=True, methods=['get'])
    def matriz_b(self, request, pk=None):
        """Matriz B (34 columnas) — modelos si materializado, borrador si no."""
        borrador = self.get_object()
        return Response(construir_matriz_b(borrador))
