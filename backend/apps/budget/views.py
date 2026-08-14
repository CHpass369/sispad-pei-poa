"""API V2 del ciclo presupuestario SIS-POA.

Fase 1 — Gestión fiscal:
    GET/POST   /api/v2/sis-poa/budget/fiscal-years/
    GET/PATCH  /api/v2/sis-poa/budget/fiscal-years/{id}/
    POST       /api/v2/sis-poa/budget/fiscal-years/{id}/enable/   → HABILITADA
    POST       /api/v2/sis-poa/budget/fiscal-years/{id}/close/    → CERRADA

Fase 2 — Techo directivo:
    GET/POST            /api/v2/sis-poa/budget/directive-ceilings/
    GET/PATCH/DELETE    /api/v2/sis-poa/budget/directive-ceilings/{id}/
    POST                .../directive-ceilings/{id}/submit/   → EN_REVISION
    POST                .../directive-ceilings/{id}/observe/  → OBSERVADO
    POST                .../directive-ceilings/{id}/approve/  → APROBADO
    POST                .../directive-ceilings/{id}/freeze/   → FIJADO
    GET                 .../directive-ceilings/{id}/composition/
    CRUD                /api/v2/sis-poa/budget/resources/         (?version=)
    CRUD                /api/v2/sis-poa/budget/mandatory-expenses/ (?version=)
    POST (multipart)    /api/v2/sis-poa/budget/documents/          (upload)
    GET                 /api/v2/sis-poa/budget/documents/?gestion=

Permisos (ADR-003):
    create/update/delete → capacidad `sis_poa.budget.manage`
    submit/observe/approve/freeze → capacidad `sis_poa.budget.approve`
    el resto usa IsAuthenticated (default global).
"""
from django.core.exceptions import ValidationError as DjangoValidationError
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiTypes, extend_schema
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import TieneCapacidad
from apps.gestion.models import GestionFiscal

from .models import (
    Allocation,
    BudgetDocument,
    CeilingResource,
    DirectiveCeiling,
    DirectiveCeilingVersion,
    DistributionVersion,
    MandatoryExpense,
    ProgrammaticCategory,
    Reserve,
)
from .serializers import (
    AllocationSerializer,
    BudgetDocumentSerializer,
    CeilingResourceSerializer,
    DirectiveCeilingSerializer,
    DistributionVersionSerializer,
    FiscalYearSerializer,
    MandatoryExpenseSerializer,
    ProgrammaticCategorySerializer,
    ReserveSerializer,
    _serializar_montos,
)
from .services import (
    ErrorDisponibilidad,
    aprobar,
    actualizar_allocation,
    cerrar_allocation,
    cerrar_gestion,
    composicion_techo,
    crear_allocation,
    crear_reserva,
    eliminar_allocation,
    enviar_a_revision,
    fijar_techo,
    gestion_habilitada,
    habilitar_gestion,
    liberar_reserva,
    observar,
    resumen_distribucion,
)

CAPACIDAD_GESTION = 'sis_poa.budget.manage'
CAPACIDAD_APROBACION = 'sis_poa.budget.approve'

ERROR_409_INMUTABLE = {
    'error': {
        'detail': 'La versión está fijada (inmutable); no se puede modificar.',
    },
}


def _respuesta_error(exception):
    return Response(
        {'error': {'detail': exception.messages}},
        status=400,
    )


def _version_actual_de(ceiling):
    return DirectiveCeilingVersion.objects.get(
        ceiling=ceiling, numero=ceiling.version_actual,
    )


class FiscalYearViewSet(viewsets.ModelViewSet):
    queryset = GestionFiscal.objects.all()
    serializer_class = FiscalYearSerializer
    filterset_fields = ['anio', 'estado', 'activa']
    search_fields = ['anio', 'descripcion']

    def get_permissions(self):
        if self.action in ('enable', 'close'):
            return [TieneCapacidad(CAPACIDAD_GESTION)]
        return super().get_permissions()

    def _ejecutar_servicio(self, request, pk, servicio):
        gestion = self.get_object()
        try:
            servicio(gestion, request.user)
        except DjangoValidationError as exc:
            return _respuesta_error(exc)
        return Response(self.get_serializer(gestion).data)

    @action(detail=True, methods=['post'], url_path='enable')
    def enable(self, request, pk=None):
        """Habilita la gestión para el ciclo presupuestario (HABILITADA)."""
        return self._ejecutar_servicio(request, pk, habilitar_gestion)

    @action(detail=True, methods=['post'], url_path='close')
    def close(self, request, pk=None):
        """Cierra la gestión del ciclo presupuestario (CERRADA)."""
        return self._ejecutar_servicio(request, pk, cerrar_gestion)


# ---------------------------------------------------------------------------
# Techo directivo
# ---------------------------------------------------------------------------
class DirectiveCeilingViewSet(viewsets.ModelViewSet):
    queryset = DirectiveCeiling.objects.select_related('gestion').all()
    serializer_class = DirectiveCeilingSerializer
    filterset_fields = ['gestion', 'estado']
    search_fields = ['gestion__anio']

    def get_permissions(self):
        if self.action in ('create', 'update', 'partial_update', 'destroy'):
            return [TieneCapacidad(CAPACIDAD_GESTION)]
        if self.action in ('submit', 'observe', 'approve', 'freeze'):
            return [TieneCapacidad(CAPACIDAD_APROBACION)]
        return super().get_permissions()

    def _ejecutar_servicio(self, request, pk, servicio, *args, **kwargs):
        ceiling = self.get_object()
        try:
            servicio(_version_actual_de(ceiling), request.user, *args, **kwargs)
        except DjangoValidationError as exc:
            return _respuesta_error(exc)
        return Response(self.get_serializer(ceiling).data)

    @action(detail=True, methods=['post'], url_path='submit')
    def submit(self, request, pk=None):
        """BORRADOR|OBSERVADO → EN_REVISION."""
        return self._ejecutar_servicio(request, pk, enviar_a_revision)

    @action(detail=True, methods=['post'], url_path='observe')
    def observe(self, request, pk=None):
        """EN_REVISION → OBSERVADO. Body: {'observaciones': 'motivo'}."""
        motivo = (
            request.data.get('observaciones') or request.data.get('motivo') or ''
        )
        if not motivo.strip():
            return Response(
                {'error': {'detail': ['Debe indicar el motivo de la observación.']}},
                status=400,
            )
        return self._ejecutar_servicio(request, pk, observar, motivo)

    @action(detail=True, methods=['post'], url_path='approve')
    def approve(self, request, pk=None):
        """EN_REVISION → APROBADO."""
        return self._ejecutar_servicio(request, pk, aprobar)

    @action(detail=True, methods=['post'], url_path='freeze')
    def freeze(self, request, pk=None):
        """APROBADO → FIJADO (valida §24, congela con checksum)."""
        observaciones = request.data.get('observaciones') or ''
        return self._ejecutar_servicio(
            request, pk, fijar_techo, observaciones,
        )


@extend_schema(
    responses={200: OpenApiTypes.OBJECT},
    description='Composición del techo directivo (§22): montos por origen, '
                'obligatorios, techo bruto y distribuible, y por fuente.',
)
class CompositionView(APIView):
    """GET /directive-ceilings/{id}/composition/ → composición del techo."""

    def get(self, request, pk):
        ceiling = get_object_or_404(DirectiveCeiling, pk=pk)
        return Response(_serializar_montos(composicion_techo(ceiling)))


class _VersionMutableMixin:
    """Rechaza create/update/delete sobre versiones fijadas (409)."""

    def _rechazo_inmutable(self, version):
        if version is None or not version.inmutable:
            return None
        return Response(ERROR_409_INMUTABLE, status=409)

    def _version_desde_datos(self, request):
        version_id = request.data.get('version')
        if not version_id:
            return None
        return DirectiveCeilingVersion.objects.filter(pk=version_id).first()

    def create(self, request, *args, **kwargs):
        rechazo = self._rechazo_inmutable(self._version_desde_datos(request))
        if rechazo:
            return rechazo
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        rechazo = self._rechazo_inmutable(self.get_object().version)
        if rechazo:
            return rechazo
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        rechazo = self._rechazo_inmutable(self.get_object().version)
        if rechazo:
            return rechazo
        return super().destroy(request, *args, **kwargs)


class CeilingResourceViewSet(_VersionMutableMixin, viewsets.ModelViewSet):
    queryset = CeilingResource.objects.select_related(
        'version', 'rubro', 'fuente', 'organismo', 'entidad_otorgante',
        'documento',
    ).all()
    serializer_class = CeilingResourceSerializer
    filterset_fields = ['version', 'origen', 'fuente']

    def get_permissions(self):
        if self.action in ('create', 'update', 'partial_update', 'destroy'):
            return [TieneCapacidad(CAPACIDAD_GESTION)]
        return super().get_permissions()


class MandatoryExpenseViewSet(_VersionMutableMixin, viewsets.ModelViewSet):
    queryset = MandatoryExpense.objects.select_related(
        'version', 'da', 'ue', 'fuente', 'organismo', 'objeto_gasto',
        'documento',
    ).all()
    serializer_class = MandatoryExpenseSerializer
    filterset_fields = ['version', 'fuente', 'programa']

    def get_permissions(self):
        if self.action in ('create', 'update', 'partial_update', 'destroy'):
            return [TieneCapacidad(CAPACIDAD_GESTION)]
        return super().get_permissions()


class BudgetDocumentViewSet(viewsets.ModelViewSet):
    queryset = BudgetDocument.objects.select_related('gestion').all()
    serializer_class = BudgetDocumentSerializer
    filterset_fields = ['gestion', 'tipo']
    search_fields = ['nombre']

    def get_permissions(self):
        if self.action in ('create', 'destroy'):
            return [TieneCapacidad(CAPACIDAD_GESTION)]
        return super().get_permissions()

    def perform_create(self, serializer):
        serializer.save()


# ---------------------------------------------------------------------------
# Fase 3 - CategorAas programAticas + catAAlogos para formularios
# ---------------------------------------------------------------------------
class ProgrammaticCategoryViewSet(viewsets.ModelViewSet):
    """CRUD de categorAas programAticas del ciclo (por gestiA3n)."""

    queryset = ProgrammaticCategory.objects.select_related('parent').all()
    serializer_class = ProgrammaticCategorySerializer
    http_method_names = ['get', 'post', 'patch', 'delete']

    def get_queryset(self):
        qs = super().get_queryset()
        gestion = self.request.query_params.get('gestion')
        if gestion:
            qs = qs.filter(gestion_id=gestion)
        nivel = self.request.query_params.get('nivel')
        if nivel:
            qs = qs.filter(nivel=nivel)
        return qs

    def perform_create(self, serializer):
        gestion = serializer.validated_data.get('gestion')
        if gestion and not gestion_habilitada(gestion):
            raise ValidationError(
                'No se pueden crear categorAas para una gestiA3n no habilitada.'
            )
        serializer.save()

    @action(detail=False, methods=['get'])
    def tree(self, request):
        """AArbol de categorAas por gestiA3n (parametro ?gestion= obligatorio)."""
        gestion = request.query_params.get('gestion')
        if not gestion:
            return Response(
                {'error': 'El parAametro ?gestion= es obligatorio.'},
                status=400,
            )
        categorias = ProgrammaticCategory.objects.filter(
            gestion_id=gestion, parent__isnull=True,
        ).order_by('nivel', 'codigo')

        def _nodo(cat):
            return {
                'id': str(cat.id),
                'codigo': cat.codigo,
                'denominacion': cat.denominacion,
                'nivel': cat.nivel,
                'estado': cat.estado,
                'hijos': [_nodo(h) for h in
                          cat.hijos.order_by('nivel', 'codigo')],
            }

        return Response([_nodo(c) for c in categorias])

    @action(detail=True, methods=['post'])
    def duplicar_a_gestion(self, request, pk=None):
        """Copia la categorAa (y su subArbol) a otra gestiA3n."""
        destino = request.data.get('gestion_destino')
        if not destino:
            return Response({'error': 'gestion_destino es obligatorio.'}, status=400)
        try:
            destino_obj = GestionFiscal.objects.get(pk=destino)
        except GestionFiscal.DoesNotExist:
            return Response({'error': 'GestiA3n destino no existe.'}, status=400)
        origen = self.get_object()
        copias = {}
        for cat in [origen, *origen.hijos.order_by('nivel', 'codigo')]:
            nuevo = ProgrammaticCategory.objects.create(
                gestion=destino_obj,
                codigo=cat.codigo,
                denominacion=cat.denominacion,
                nivel=cat.nivel,
                parent=copias.get(cat.parent_id),
                vigencia_desde=cat.vigencia_desde,
                vigencia_hasta=cat.vigencia_hasta,
                estado=cat.estado,
                origen=cat.origen or 'duplicado',
                normativa=cat.normativa,
            )
            copias[cat.id] = nuevo
        return Response({'detail': f'CategorAa y {len(copias)-1} hijos duplicados.'}, status=201)


class CatalogOptionsView(APIView):
    """CAtAlogos corporativos para poblar selects del ciclo presupuestario.

    GET /api/v2/sis-poa/budget/catalogs/ -> {fuentes, organismos, rubros,
    objetos_gasto, distritos, da, ue, unidades}
    """

    def get(self, request):
        from apps.catalogos.models import (
            EntidadTransferencia,
            FuenteFinanciamiento,
            ObjetoGasto,
            OrganismoFinanciador,
            RubroRecurso,
        )
        from apps.organizacion.models import (
            DireccionAdministrativa,
            UnidadEjecutora,
            UnidadOrganizacional,
        )
        from apps.territorio.models import Distrito

        gestion = request.query_params.get('gestion')

        def _opts(qs, codigo='codigo', nombre='denominacion'):
            return [
                {'id': str(o.pk), 'codigo': getattr(o, codigo), 'nombre': getattr(o, nombre)}
                for o in qs[:500]
            ]

        data = {
            'fuentes': _opts(FuenteFinanciamiento.objects.all()),
            'organismos': _opts(OrganismoFinanciador.objects.all()),
            'rubros': _opts(RubroRecurso.objects.all()),
            'objetos_gasto': _opts(ObjetoGasto.objects.all()),
            'entidades_transferencia': _opts(EntidadTransferencia.objects.all()),
            'distritos': _opts(Distrito.objects.all(), codigo='codigo', nombre='nombre'),
            'direcciones': _opts(DireccionAdministrativa.objects.all(), nombre='nombre'),
            'unidades_ejecutoras': _opts(UnidadEjecutora.objects.all(), nombre='nombre'),
            'unidades_organizacionales': _opts(
                UnidadOrganizacional.objects.all(), nombre='nombre'),
        }
        return Response(data)


# ---------------------------------------------------------------------------
# Fase 4 - Distribución presupuestaria (versiones, aperturas, reservas)
# ---------------------------------------------------------------------------

def _respuesta_exceso(exc):
    """400 BUDGET_EXCEEDED: {error: {detail}, code, details}."""
    return Response(
        {
            'error': {'detail': exc.messages},
            'code': exc.code,
            'details': exc.details,
        },
        status=400,
    )


class DistributionVersionViewSet(viewsets.ModelViewSet):
    """Versiones de distribución (CRUD liviano + listado por gestión)."""

    queryset = DistributionVersion.objects.select_related(
        'gestion', 'fijado_por',
    ).all()
    serializer_class = DistributionVersionSerializer
    filterset_fields = ['gestion', 'estado', 'inmutable']
    search_fields = ['gestion__anio']

    def get_permissions(self):
        if self.action in ('create', 'update', 'partial_update', 'destroy'):
            return [TieneCapacidad(CAPACIDAD_GESTION)]
        return super().get_permissions()

    def perform_create(self, serializer):
        request = self.context.get('request')
        usuario = request.user if request and request.user.is_authenticated else None
        serializer.save(created_by=usuario, updated_by=usuario)

    def destroy(self, request, *args, **kwargs):
        version = self.get_object()
        if version.inmutable:
            return Response(ERROR_409_INMUTABLE, status=409)
        return super().destroy(request, *args, **kwargs)

    @action(detail=False, methods=['get'], url_path='versions')
    def versions(self, request):
        """Lista las versiones de distribución por gestión (?gestion=)."""
        gestion = request.query_params.get('gestion')
        if not gestion:
            return Response(
                {'error': {'detail': ['El parámetro ?gestion= es obligatorio.']}},
                status=400,
            )
        qs = self.get_queryset().filter(gestion_id=gestion).order_by('-numero')
        return Response(self.get_serializer(qs, many=True).data)


class AllocationViewSet(viewsets.ModelViewSet):
    """Aperturas programáticas: CRUD con fuentes anidadas + cerrar.

    create/update aceptan `fuentes`: [{fuente, organismo, monto}]. Errores
    de disponibilidad → 400 {error: {detail}, code: 'BUDGET_EXCEEDED',
    details: {requested, available, difference}}.
    """

    queryset = Allocation.objects.select_related(
        'gestion', 'version', 'unidad_organizacional', 'distrito',
        'da', 'ue', 'categoria',
    ).prefetch_related('fuentes__fuente', 'fuentes__organismo').all()
    serializer_class = AllocationSerializer
    filterset_fields = ['gestion', 'version', 'distrito', 'categoria', 'estado']
    search_fields = ['denominacion', 'codigo_sisin', 'proyecto_codigo',
                     'actividad_codigo']

    def get_permissions(self):
        if self.action in ('create', 'update', 'partial_update', 'destroy',
                           'cerrar'):
            return [TieneCapacidad(CAPACIDAD_GESTION)]
        return super().get_permissions()

    def _validar_y_servicio(self, request, serializer, allocation=None):
        """Valida el serializer y ejecuta el servicio de dominio mapeando
        errores: BUDGET_EXCEEDED → 400 con code/details; resto → 400 genérico."""
        gestion = serializer.validated_data.get('gestion')
        if gestion is None and allocation is not None:
            gestion = allocation.gestion
        if gestion is None:
            return Response(
                {'error': {'detail': ['La gestión es obligatoria.']}},
                status=400,
            )
        datos = {
            k: v for k, v in serializer.validated_data.items() if k != 'gestion'
        }
        try:
            if allocation is None:
                resultado = crear_allocation(gestion, request.user, datos)
            else:
                resultado = actualizar_allocation(
                    allocation, request.user, datos,
                )
        except ErrorDisponibilidad as exc:
            return _respuesta_exceso(exc)
        except DjangoValidationError as exc:
            return _respuesta_error(exc)
        return Response(
            self.get_serializer(resultado).data,
            status=201 if allocation is None else 200,
        )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return self._validar_y_servicio(request, serializer)

    def update(self, request, *args, **kwargs):
        allocation = self.get_object()
        partial = kwargs.get('partial', False)
        serializer = self.get_serializer(
            allocation, data=request.data, partial=partial,
        )
        serializer.is_valid(raise_exception=True)
        return self._validar_y_servicio(request, serializer, allocation)

    def destroy(self, request, *args, **kwargs):
        allocation = self.get_object()
        try:
            eliminar_allocation(allocation, request.user)
        except DjangoValidationError as exc:
            return _respuesta_error(exc)
        return Response(status=204)

    @action(detail=True, methods=['post'], url_path='cerrar')
    def cerrar(self, request, pk=None):
        """Cierra la apertura (solo si no excede el disponible)."""
        allocation = self.get_object()
        try:
            cerrar_allocation(allocation, request.user)
        except ErrorDisponibilidad as exc:
            return _respuesta_exceso(exc)
        except DjangoValidationError as exc:
            return _respuesta_error(exc)
        return Response(self.get_serializer(allocation).data)


class ReserveViewSet(viewsets.ModelViewSet):
    """Reservas presupuestarias: CRUD + acción liberar."""

    queryset = Reserve.objects.select_related(
        'gestion', 'version', 'fuente', 'organismo',
    ).all()
    serializer_class = ReserveSerializer
    filterset_fields = ['gestion', 'version', 'estado', 'tipo', 'fuente']
    search_fields = ['motivo']

    def get_permissions(self):
        if self.action in ('create', 'update', 'partial_update', 'destroy',
                           'liberar'):
            return [TieneCapacidad(CAPACIDAD_GESTION)]
        return super().get_permissions()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        gestion = serializer.validated_data.get('gestion')
        if gestion is None:
            return Response(
                {'error': {'detail': ['La gestión es obligatoria.']}},
                status=400,
            )
        datos = {
            k: v for k, v in serializer.validated_data.items() if k != 'gestion'
        }
        try:
            reserva = crear_reserva(gestion, request.user, datos)
        except ErrorDisponibilidad as exc:
            return _respuesta_exceso(exc)
        except DjangoValidationError as exc:
            return _respuesta_error(exc)
        return Response(self.get_serializer(reserva).data, status=201)

    @action(detail=True, methods=['post'], url_path='liberar')
    def liberar(self, request, pk=None):
        """Libera la reserva (devuelve el disponible a la fuente)."""
        reserva = self.get_object()
        try:
            liberar_reserva(reserva, request.user)
        except DjangoValidationError as exc:
            return _respuesta_error(exc)
        return Response(self.get_serializer(reserva).data)


@extend_schema(
    responses={200: OpenApiTypes.OBJECT},
    description='Resumen de la distribución (§48): cards + tabla por fuente.',
)
class DistributionDashboardView(APIView):
    """GET /distributions/dashboard/?gestion= → resumen_distribucion."""

    def get(self, request):
        gestion = request.query_params.get('gestion')
        if not gestion:
            return Response(
                {'error': {'detail': ['El parámetro ?gestion= es obligatorio.']}},
                status=400,
            )
        gestion_obj = get_object_or_404(GestionFiscal, pk=gestion)
        return Response(_serializar_montos(resumen_distribucion(gestion_obj)))
