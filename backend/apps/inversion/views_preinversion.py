"""API V2 del dominio de preinversión SIS-PRO (SISPRE / RM 115).

Endpoints del expediente: ITCP, TDR, EDTP, componentes, beneficiarios,
documentos, revisiones, observaciones, aprobaciones y acciones del ciclo
(clasificar, inicializar, madurez, generación documental, transferencia).
"""
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response

from apps.accounts.permissions import TieneAlgunaCapacidad

from .documentos_preinversion import ErrorGeneracionDocumento, generar_documento
from .models_preinversion import (
    ActividadTDR,
    AlternativaProyecto,
    AprobacionPreinversion,
    ComponenteProyecto,
    CondicionITCP,
    DocumentoGenerado,
    DocumentoPreinversion,
    EDTP,
    EstudioTecnico,
    FuenteFinanciamientoEDTP,
    GrupoBeneficiario,
    IndicadorEvaluacionEDTP,
    ITCP,
    ItemCostoEDTP,
    ItemCronograma,
    ItemPresupuestoTDR,
    ObservacionPreinversion,
    PersonalTDR,
    PlanOperacionMantenimiento,
    ProductoTDR,
    RevisionPreinversion,
    SeccionEDTP,
    SolicitudReformulacion,
    TDR,
)
from .models_v2 import EstadosExpedientePreinversion, Proyecto
from .views_v2 import ProyectoSerializer
from .serializers_preinversion import (
    AlternativaProyectoSerializer,
    AprobacionSerializer,
    ComponenteProyectoSerializer,
    CondicionITCPSerializer,
    DocumentoGeneradoSerializer,
    DocumentoPreinversionSerializer,
    EDTPSerializer,
    EstudioTecnicoSerializer,
    FuenteFinanciamientoSerializer,
    GrupoBeneficiarioSerializer,
    IndicadorEvaluacionSerializer,
    ItemCostoEDTPSerializer,
    ItemCronogramaSerializer,
    ITCPSerializer,
    ObservacionSerializer,
    PlanOMSerializer,
    RevisionSerializer,
    SeccionEDTPSerializer,
    SolicitudReformulacionSerializer,
    TDRActividadSerializer,
    TDRItemPresupuestoSerializer,
    TDRPersonalSerializer,
    TDRProductoSerializer,
    TDRSerializer,
)
from .services_preinversion import (
    calcular_madurez,
    clasificar_tipologia,
    construir_paquete_transferencia,
    inicializar_edtp,
    inicializar_itcp,
    validar_edtp_para_aprobacion,
    validar_itcp_para_aprobacion,
)

CAPACIDADES_ESCRITURA = ['sis_pro.project.create', 'sis_pro.project.edit']
CAPACIDADES_VALIDACION = ['sis_pro.preinvestment.validate']


def _permisos(*capacidades):
    return [TieneAlgunaCapacidad(*capacidades)]


class _BasePreinversionViewSet(viewsets.ModelViewSet):
    def get_permissions(self):
        if self.action in ('create', 'update', 'partial_update', 'destroy'):
            return _permisos(*CAPACIDADES_ESCRITURA)
        return super().get_permissions()

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user, updated_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)


# ---------------------------------------------------------------------------
# Acciones del ciclo sobre Proyecto
# ---------------------------------------------------------------------------
class ProyectoPreinversionViewSet(_BasePreinversionViewSet):
    """Extiende SIS-PRO V2 con acciones de preinversión."""

    queryset = Proyecto.objects.all()
    serializer_class = ProyectoSerializer
    filterset_fields = [
        'gestion', 'fase', 'estado', 'estado_preinversion',
        'tipologia_rm115', 'distrito', 'habilitado_poa',
    ]

    ACCIONES_VALIDACION = {
        'inicializar_itcp', 'inicializar_edtp', 'calcular_madurez',
        'validar_aprobacion', 'generar_documento', 'solicitar_reformulacion',
        'cambiar_estado', 'clasificar',
    }

    def get_permissions(self):
        if self.action in ('create', 'update', 'partial_update', 'destroy'):
            return _permisos(*CAPACIDADES_ESCRITURA)
        if self.action in self.ACCIONES_VALIDACION:
            return _permisos(*CAPACIDADES_ESCRITURA, *CAPACIDADES_VALIDACION)
        return super().get_permissions()

    @action(detail=True, methods=['post'])
    def clasificar(self, request, pk=None):
        proyecto = self.get_object()
        sugerida = clasificar_tipologia(proyecto)
        if request.data.get('aceptar', True):
            proyecto.tipologia_rm115 = sugerida
            proyecto.save(update_fields=['tipologia_rm115', 'updated_at'])
        return Response({
            'tipologia_sugerida': sugerida,
            'aceptada': request.data.get('aceptar', True),
        })

    @action(detail=True, methods=['post'])
    def inicializar_itcp(self, request, pk=None):
        itcp = inicializar_itcp(self.get_object(), request.user)
        return Response(
            {'itcp_id': itcp.id, 'condiciones': itcp.condiciones.count()},
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=['post'])
    def inicializar_edtp(self, request, pk=None):
        edtp = inicializar_edtp(self.get_object(), request.user)
        return Response(
            {'edtp_id': edtp.id, 'secciones': edtp.secciones.count()},
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=['post'])
    def calcular_madurez(self, request, pk=None):
        proyecto = self.get_object()
        puntaje = calcular_madurez(proyecto)
        return Response({
            'puntaje_madurez': puntaje,
            'habilitado_poa': proyecto.habilitado_poa,
            'estado_preinversion': proyecto.estado_preinversion,
        })

    @action(detail=True, methods=['post'])
    def validar_aprobacion(self, request, pk=None):
        proyecto = self.get_object()
        itcp = getattr(proyecto, 'itcp', None)
        edtp = getattr(proyecto, 'edtp', None)
        if request.data.get('documento') == 'EDTP':
            if edtp is None:
                return Response(
                    {'error': 'El proyecto no tiene EDTP'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            errores = validar_edtp_para_aprobacion(edtp)
        else:
            if itcp is None:
                return Response(
                    {'error': 'El proyecto no tiene ITCP'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            errores = validar_itcp_para_aprobacion(itcp)
        return Response({
            'aprobable': not errores,
            'errores': errores,
            'estado_preinversion': proyecto.estado_preinversion,
        })

    @action(detail=True, methods=['post'])
    def generar_documento(self, request, pk=None):
        tipo = request.data.get('tipo_documento')
        if tipo not in {'ITCP', 'EDTP'}:
            return Response(
                {'error': 'tipo_documento debe ser ITCP o EDTP'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            generado = generar_documento(self.get_object(), tipo)
        except ErrorGeneracionDocumento as exc:
            return Response(
                {'error': str(exc)}, status=status.HTTP_400_BAD_REQUEST,
            )
        return Response({
            'documento_generado_id': generado.id,
            'estado': generado.estado,
        }, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get'])
    def paquete_transferencia(self, request, pk=None):
        return Response(construir_paquete_transferencia(self.get_object()))

    @action(detail=True, methods=['post'])
    def solicitar_reformulacion(self, request, pk=None):
        serializer = SolicitudReformulacionSerializer(
            data={**request.data, 'proyecto': self.get_object().id},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save(created_by=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'])
    def elegibles_poa(self, request):
        qs = self.filter_queryset(
            self.get_queryset().filter(habilitado_poa=True)
        )
        return Response(self.get_serializer(qs, many=True).data)

    @action(detail=True, methods=['post'])
    def cambiar_estado(self, request, pk=None):
        """Transición controlada del estado del expediente de preinversión."""
        proyecto = self.get_object()
        nuevo = request.data.get('estado_preinversion')
        validos = [c[0] for c in EstadosExpedientePreinversion.CHOICES]
        if nuevo not in validos:
            return Response(
                {'error': f'estado_preinversion inválido: {nuevo}'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        proyecto.estado_preinversion = nuevo
        proyecto.save(update_fields=['estado_preinversion', 'updated_at'])
        return Response(self.get_serializer(proyecto).data)


# ---------------------------------------------------------------------------
# ITCP
# ---------------------------------------------------------------------------
class ITCPViewSet(_BasePreinversionViewSet):
    queryset = ITCP.objects.select_related('proyecto').prefetch_related('condiciones')
    serializer_class = ITCPSerializer
    filterset_fields = ['proyecto', 'estado']


class CondicionITCPViewSet(_BasePreinversionViewSet):
    queryset = CondicionITCP.objects.select_related('itcp', 'proyecto')
    serializer_class = CondicionITCPSerializer
    filterset_fields = ['itcp', 'proyecto', 'categoria', 'estado', 'critica']
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def perform_update(self, serializer):
        archivo = self.request.FILES.get('archivo')
        if archivo:
            serializer.save(
                archivo=archivo,
                nombre_archivo=archivo.name,
                updated_by=self.request.user,
            )
        else:
            serializer.save(updated_by=self.request.user)


# ---------------------------------------------------------------------------
# TDR
# ---------------------------------------------------------------------------
class TDRViewSet(_BasePreinversionViewSet):
    queryset = TDR.objects.select_related('proyecto').prefetch_related(
        'actividades', 'productos', 'personal', 'items_presupuesto',
    )
    serializer_class = TDRSerializer
    filterset_fields = ['proyecto', 'estado']


class TDRActividadViewSet(_BasePreinversionViewSet):
    queryset = ActividadTDR.objects.select_related('tdr')
    serializer_class = TDRActividadSerializer
    filterset_fields = ['tdr']


class TDRProductoViewSet(_BasePreinversionViewSet):
    queryset = ProductoTDR.objects.select_related('tdr')
    serializer_class = TDRProductoSerializer
    filterset_fields = ['tdr']


class TDRPersonalViewSet(_BasePreinversionViewSet):
    queryset = PersonalTDR.objects.select_related('tdr')
    serializer_class = TDRPersonalSerializer
    filterset_fields = ['tdr']


class TDRItemPresupuestoViewSet(_BasePreinversionViewSet):
    queryset = ItemPresupuestoTDR.objects.select_related('tdr')
    serializer_class = TDRItemPresupuestoSerializer
    filterset_fields = ['tdr']


# ---------------------------------------------------------------------------
# EDTP
# ---------------------------------------------------------------------------
class EDTPViewSet(_BasePreinversionViewSet):
    queryset = EDTP.objects.select_related('proyecto').prefetch_related(
        'secciones', 'estudios_tecnicos', 'items_costo', 'fuentes_financiamiento',
        'indicadores_evaluacion',
    )
    serializer_class = EDTPSerializer
    filterset_fields = ['proyecto', 'estado', 'resultado_viabilidad']


class SeccionEDTPViewSet(_BasePreinversionViewSet):
    queryset = SeccionEDTP.objects.select_related('edtp')
    serializer_class = SeccionEDTPSerializer
    filterset_fields = ['edtp', 'estado', 'requerida', 'aplicable']


class EstudioTecnicoViewSet(_BasePreinversionViewSet):
    queryset = EstudioTecnico.objects.select_related('edtp')
    serializer_class = EstudioTecnicoSerializer
    filterset_fields = ['edtp', 'estado', 'requerido']


class ItemCostoEDTPViewSet(_BasePreinversionViewSet):
    queryset = ItemCostoEDTP.objects.select_related('edtp', 'componente')
    serializer_class = ItemCostoEDTPSerializer
    filterset_fields = ['edtp', 'componente', 'categoria']


class FuenteFinanciamientoViewSet(_BasePreinversionViewSet):
    queryset = FuenteFinanciamientoEDTP.objects.select_related('edtp')
    serializer_class = FuenteFinanciamientoSerializer
    filterset_fields = ['edtp', 'confirmada']


class ItemCronogramaViewSet(_BasePreinversionViewSet):
    queryset = ItemCronograma.objects.select_related('edtp', 'componente')
    serializer_class = ItemCronogramaSerializer
    filterset_fields = ['edtp', 'componente']


class PlanOMViewSet(_BasePreinversionViewSet):
    queryset = PlanOperacionMantenimiento.objects.select_related('edtp')
    serializer_class = PlanOMSerializer
    filterset_fields = ['edtp']


class IndicadorEvaluacionViewSet(_BasePreinversionViewSet):
    queryset = IndicadorEvaluacionEDTP.objects.select_related('edtp')
    serializer_class = IndicadorEvaluacionSerializer
    filterset_fields = ['edtp', 'tipo_indicador']


# ---------------------------------------------------------------------------
# Componentes / beneficiarios / alternativas
# ---------------------------------------------------------------------------
class ComponenteProyectoViewSet(_BasePreinversionViewSet):
    queryset = ComponenteProyecto.objects.select_related('proyecto')
    serializer_class = ComponenteProyectoSerializer
    filterset_fields = ['proyecto']


class GrupoBeneficiarioViewSet(_BasePreinversionViewSet):
    queryset = GrupoBeneficiario.objects.select_related('proyecto')
    serializer_class = GrupoBeneficiarioSerializer
    filterset_fields = ['proyecto', 'tipo']


class AlternativaProyectoViewSet(_BasePreinversionViewSet):
    queryset = AlternativaProyecto.objects.select_related('proyecto')
    serializer_class = AlternativaProyectoSerializer
    filterset_fields = ['proyecto']


# ---------------------------------------------------------------------------
# Documentos
# ---------------------------------------------------------------------------
class DocumentoPreinversionViewSet(_BasePreinversionViewSet):
    queryset = DocumentoPreinversion.objects.select_related(
        'proyecto'
    ).prefetch_related('versiones')
    serializer_class = DocumentoPreinversionSerializer
    filterset_fields = ['proyecto', 'tipo_documento', 'etapa', 'estado']


class DocumentoGeneradoViewSet(viewsets.ReadOnlyModelViewSet):
    """Historial de documentos generados (inventario documental)."""

    queryset = DocumentoGenerado.objects.select_related('proyecto')
    serializer_class = DocumentoGeneradoSerializer
    filterset_fields = ['proyecto', 'tipo_documento', 'estado']


# ---------------------------------------------------------------------------
# Revisión / observación / aprobación
# ---------------------------------------------------------------------------
class RevisionViewSet(_BasePreinversionViewSet):
    queryset = RevisionPreinversion.objects.select_related('proyecto')
    serializer_class = RevisionSerializer
    filterset_fields = ['proyecto', 'etapa', 'tipo_revision', 'estado']


class ObservacionViewSet(_BasePreinversionViewSet):
    queryset = ObservacionPreinversion.objects.select_related(
        'proyecto', 'revision',
    )
    serializer_class = ObservacionSerializer
    filterset_fields = ['proyecto', 'revision', 'severidad', 'estado']


class AprobacionViewSet(_BasePreinversionViewSet):
    queryset = AprobacionPreinversion.objects.select_related('proyecto')
    serializer_class = AprobacionSerializer
    filterset_fields = ['proyecto', 'etapa', 'nivel_aprobacion', 'estado']
