"""API V2 del SIS-POA (WP-10 / /api/v2/sis-poa/).

F2b: aplica `CapacidadConScope` (ADR-003) y filtra el queryset por la UO
efectiva del usuario. Cierra la vulnerabilidad por la que cualquier usuario
con `sis_poa.formulate` veía todas las POAUs del sistema.
"""
from django.db.models import Q
from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from apps.accounts.permissions import (
    CapacidadConScope,
    GESTION_INVALIDA,
    resolver_gestion_id,
)
from apps.accounts.services_scope import GLOBAL_SCOPE, ScopeResolver
from apps.gestion.models import GestionFiscal
from apps.poau.migration_v2 import resumen_presupuesto, validar_techo
from apps.poau.models_v2 import (
    AccionCortoPlazo,
    Actividad,
    Operacion,
    PoAInstitucional,
    ProgramacionActividad,
    Tarea,
)

# (capacidad_view, capacidad_edit) por nombre de ViewSet.
# Los códigos usan la convención F1 `<sistema>.<dominio>.<accion>`.
CAPACIDADES_POR_VIEWSET = {
    'PoAViewSet': ('sis_poa.poa.view', 'sis_poa.poa.edit'),
    'AccionViewSet': ('sis_poa.poau.view', 'sis_poa.poau.edit'),
    'OperacionViewSet': ('sis_poa.poau.view', 'sis_poa.poau.edit'),
    'ActividadViewSet': ('sis_poa.poau.view', 'sis_poa.poau.edit'),
    'TareaViewSet': ('sis_poa.poau.view', 'sis_poa.poau.edit'),
    'ProgramacionViewSet': ('sis_poa.poau.view', 'sis_poa.poau.edit'),
}

_GESTION_REQUEST_ATTR = '_poau_gestion_fiscal'


def _gestion_fiscal(request):
    """Resolve and cache the canonical fiscal year for this request."""
    if hasattr(request, _GESTION_REQUEST_ATTR):
        return getattr(request, _GESTION_REQUEST_ATTR)
    gestion_id = resolver_gestion_id(request)
    if gestion_id in (None, GESTION_INVALIDA):
        gestion = GESTION_INVALIDA
    else:
        gestion = GestionFiscal.objects.filter(pk=gestion_id).only('id', 'anio').first()
        if gestion is None:
            gestion = GESTION_INVALIDA
    setattr(request, _GESTION_REQUEST_ATTR, gestion)
    return gestion


class CapacidadConGestionFiscal(CapacidadConScope):
    """Require a real fiscal year before capability or superuser evaluation."""

    def _gestion_id(self, request, view):
        gestion = _gestion_fiscal(request)
        return GESTION_INVALIDA if gestion is GESTION_INVALIDA else gestion.pk

    def has_permission(self, request, view):
        if _gestion_fiscal(request) is GESTION_INVALIDA:
            return False
        return super().has_permission(request, view)


def _queryset_fiscal(request, queryset, year_lookup):
    """Filter effective scopes and records with the same fiscal context."""
    gestion = _gestion_fiscal(request)
    if gestion is GESTION_INVALIDA:
        return queryset.none(), set()
    queryset = queryset.filter(**{year_lookup: gestion.anio})
    if request.user.is_superuser:
        return queryset, None
    unidades = ScopeResolver.unidades_efectivas(request.user, gestion.pk)
    return queryset, None if GLOBAL_SCOPE in unidades else unidades


class PoASerializer(serializers.ModelSerializer):
    class Meta:
        model = PoAInstitucional
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

    def _validar(self, validated_data):
        from django.core.exceptions import ValidationError as ModelValidationError
        try:
            return super().create(validated_data)
        except ModelValidationError as exc:
            raise serializers.ValidationError(exc.message_dict)

    def create(self, validated_data):
        return self._validar(validated_data)

    def update(self, instance, validated_data):
        from django.core.exceptions import ValidationError as ModelValidationError
        try:
            return super().update(instance, validated_data)
        except ModelValidationError as exc:
            raise serializers.ValidationError(exc.message_dict)


class AccionSerializer(serializers.ModelSerializer):
    # `nodo_pei` lo retiro `poau/0006_remove_kernel_v2_fks` junto con el nucleo
    # estrategico. Volvera cuando se reconstruya SIS-PE; hasta entonces el
    # serializer no puede nombrarlo.
    class Meta:
        model = AccionCortoPlazo
        fields = [
            'id', 'poa', 'codigo', 'nombre', 'descripcion',
            'unidad', 'atributos', 'estado',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class OperacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Operacion
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class ActividadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Actividad
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class TareaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tarea
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class ProgramacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProgramacionActividad
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


def _permisos_para_viewset(viewset_cls, action):
    """Permission classes específicas por (ViewSet, action).

    - list/retrieve: capacidad_view.
    - create/update/destroy: capacidad_edit.
    """
    cap_view, cap_edit = CAPACIDADES_POR_VIEWSET[viewset_cls.__name__]
    codigo = cap_edit if action in ('create', 'update', 'partial_update', 'destroy') else cap_view
    return [CapacidadConGestionFiscal(codigo, gestion_id_param='gestion_id')]


def _autorizar_uo_destino(user, unidad_id):
    """Verifica que el usuario puede operar sobre la UO destino.

    Usado en `perform_create` y `perform_update` para impedir mover el
    objeto a una UO fuera de su alcance organizacional. Lanza 403 si la
    UO existe pero está fuera del alcance (no es validación de datos:
    es autorización).
    """
    if not unidad_id:
        return  # UO nula permitida (caso Operacion sin unidad propia).
    if user.is_superuser:
        return
    unidades = ScopeResolver.unidades_efectivas(user)
    if GLOBAL_SCOPE in unidades:
        return
    if not ScopeResolver.puede_operar(user, unidad_id):
        raise PermissionDenied(
            'Unidad organizacional fuera de su alcance.',
        )


class PoAViewSet(viewsets.ModelViewSet):
    queryset = PoAInstitucional.objects.all()
    serializer_class = PoASerializer
    filterset_fields = ['gestion', 'estado']

    def get_permissions(self):
        return _permisos_para_viewset(PoAViewSet, self.action)

    def get_queryset(self):
        queryset, unidades = _queryset_fiscal(
            self.request, self.queryset, 'gestion',
        )
        if unidades is None:
            return queryset
        if not unidades:
            return queryset.none()
        # PoA: filtro EXISTS sobre sus AccionCortoPlazo.unidad.
        # detail exige TODAS las acciones en alcance (`has_object_permission`
        # en CapacidadConScope ya lo valida).
        return queryset.filter(acciones__unidad_id__in=unidades).distinct()

    @action(detail=True, methods=['get'])
    def acciones(self, request, pk=None):
        poa = self.get_object()
        acciones = poa.acciones.select_related('unidad')
        serializer = AccionSerializer(acciones, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def resumen_presupuesto(self, request, pk=None):
        return Response(resumen_presupuesto(self.get_object()))

    @action(detail=True, methods=['get'])
    def validar_techo(self, request, pk=None):
        return Response(validar_techo(self.get_object()))

    @action(detail=True, methods=['get'])
    def programaciones(self, request, pk=None):
        """Programaciones físico-financieras por actividad del POA."""
        poa = self.get_object()
        from django.db.models import Sum
        filas = (
            ProgramacionActividad.objects.filter(
                actividad__operacion__accion__poa=poa,
            )
            .values('actividad_id', 'anio', 'tipo')
            .annotate(
                programado=Sum('programado'),
                ejecutado=Sum('ejecutado'),
            )
            .order_by('actividad_id', 'anio', 'tipo')
        )
        actividades = {
            str(a.id): {'codigo': a.codigo, 'nombre': a.nombre}
            for a in Actividad.objects.filter(
                operacion__accion__poa=poa,
            )
        }
        return Response({
            'poa': str(poa.id),
            'codigo': poa.codigo,
            'filas': [
                {
                    'actividad_id': str(f['actividad_id']),
                    'actividad_codigo': actividades.get(str(f['actividad_id']), {}).get('codigo'),
                    'actividad_nombre': actividades.get(str(f['actividad_id']), {}).get('nombre'),
                    'anio': f['anio'],
                    'tipo': f['tipo'],
                    'programado': str(f['programado'] or 0),
                    'ejecutado': str(f['ejecutado'] or 0),
                }
                for f in filas
            ],
        })


class AccionViewSet(viewsets.ModelViewSet):
    queryset = AccionCortoPlazo.objects.select_related('poa')
    serializer_class = AccionSerializer
    filterset_fields = ['poa', 'estado']

    def get_permissions(self):
        return _permisos_para_viewset(AccionViewSet, self.action)

    def get_queryset(self):
        queryset, unidades = _queryset_fiscal(
            self.request, self.queryset, 'poa__gestion',
        )
        if unidades is None:
            return queryset
        if not unidades:
            return queryset.none()
        return queryset.filter(unidad_id__in=unidades)

    def perform_create(self, serializer):
        unidad = serializer.validated_data.get('unidad')
        _autorizar_uo_destino(self.request.user, unidad.id if unidad else None)
        serializer.save()

    def perform_update(self, serializer):
        instancia = serializer.instance
        # Si cambia `unidad`, validar la nueva; si no, validar la actual.
        nueva_uo = serializer.validated_data.get('unidad', instancia.unidad)
        _autorizar_uo_destino(self.request.user, nueva_uo.id if nueva_uo else None)
        serializer.save()


class OperacionViewSet(viewsets.ModelViewSet):
    queryset = Operacion.objects.select_related('accion', 'unidad')
    serializer_class = OperacionSerializer
    filterset_fields = ['accion', 'estado']

    def get_permissions(self):
        return _permisos_para_viewset(OperacionViewSet, self.action)

    def get_queryset(self):
        queryset, unidades = _queryset_fiscal(
            self.request, self.queryset, 'accion__poa__gestion',
        )
        if unidades is None:
            return queryset
        if not unidades:
            return queryset.none()
        # Operacion.unidad es nullable: si tiene UO propia filtra por ella;
        # si no, cae a la UO de la Accion padre.
        return queryset.filter(
            Q(unidad_id__in=unidades)
            | Q(unidad_id__isnull=True, accion__unidad_id__in=unidades)
        )

    def perform_create(self, serializer):
        unidad = serializer.validated_data.get('unidad')
        if unidad:
            _autorizar_uo_destino(self.request.user, unidad.id)
        else:
            # Sin UO propia: validar la UO de la acción padre.
            accion = serializer.validated_data.get('accion')
            if accion and accion.unidad_id:
                _autorizar_uo_destino(self.request.user, accion.unidad_id)
        serializer.save()


class ActividadViewSet(viewsets.ModelViewSet):
    queryset = Actividad.objects.select_related('operacion')
    serializer_class = ActividadSerializer
    filterset_fields = ['operacion', 'estado']

    def get_permissions(self):
        return _permisos_para_viewset(ActividadViewSet, self.action)

    def get_queryset(self):
        queryset, unidades = _queryset_fiscal(
            self.request, self.queryset, 'operacion__accion__poa__gestion',
        )
        if unidades is None:
            return queryset
        if not unidades:
            return queryset.none()
        # Actividad no tiene UO propia: sube por operacion → accion → unidad.
        return queryset.filter(
            operacion__accion__unidad_id__in=unidades
        )


class TareaViewSet(viewsets.ModelViewSet):
    queryset = Tarea.objects.select_related('actividad')
    serializer_class = TareaSerializer
    filterset_fields = ['actividad', 'estado']

    def get_permissions(self):
        return _permisos_para_viewset(TareaViewSet, self.action)

    def get_queryset(self):
        queryset, unidades = _queryset_fiscal(
            self.request,
            self.queryset,
            'actividad__operacion__accion__poa__gestion',
        )
        if unidades is None:
            return queryset
        if not unidades:
            return queryset.none()
        return queryset.filter(
            actividad__operacion__accion__unidad_id__in=unidades
        )


class ProgramacionViewSet(viewsets.ModelViewSet):
    queryset = ProgramacionActividad.objects.select_related('actividad')
    serializer_class = ProgramacionSerializer
    filterset_fields = ['actividad', 'anio', 'tipo']

    def get_permissions(self):
        return _permisos_para_viewset(ProgramacionViewSet, self.action)

    def get_queryset(self):
        queryset, unidades = _queryset_fiscal(
            self.request,
            self.queryset,
            'actividad__operacion__accion__poa__gestion',
        )
        if unidades is None:
            return queryset
        if not unidades:
            return queryset.none()
        return queryset.filter(
            actividad__operacion__accion__unidad_id__in=unidades
        )
