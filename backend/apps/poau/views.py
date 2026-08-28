from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Prefetch
from django.shortcuts import get_object_or_404

from apps.accounts.permissions import (
    CapacidadConScope, GESTION_INVALIDA, resolve_unidad_id,
    resolver_gestion_id,
)
from apps.accounts.services_scope import GLOBAL_SCOPE, ScopeResolver
from apps.gestion.mixins import CandadoSisPoaMixin, gestion_del_candado
from apps.organizacion.models import UnidadOrganizacional

from .models import POAU, POAUActividad, EjecucionFisica, EjecucionFinanciera
from .serializers import (
    POAUSerializer, POAUListSerializer, POAUActividadSerializer,
    EjecucionFisicaSerializer, EjecucionFinancieraSerializer,
)


CAPACIDADES_POR_ACCION = {
    'create': 'sis_poa.poau.create',
    'update': 'sis_poa.poau.edit',
    'partial_update': 'sis_poa.poau.edit',
    'destroy': 'sis_poa.poau.edit',
    'enviar': 'sis_poa.poau.submit',
    'aprobar': 'sis_poa.poau.approve',
    'rechazar': 'sis_poa.poau.review',
}


def _unidades_efectivas_o_none(request):
    user = request.user
    if user.is_superuser:
        return None
    gestion_id = resolver_gestion_id(request)
    if gestion_id is GESTION_INVALIDA:
        return set()
    unidades = ScopeResolver.unidades_efectivas(user, gestion_id)
    return None if GLOBAL_SCOPE in unidades else unidades


def _autorizar_objetivo(request, objetivo):
    if request.user.is_superuser:
        return
    unidad_id = objetivo.pk if isinstance(
        objetivo, UnidadOrganizacional,
    ) else resolve_unidad_id(objetivo)
    gestion_id = resolver_gestion_id(request)
    if (
        unidad_id is None or gestion_id is GESTION_INVALIDA
        or not ScopeResolver.puede_operar(request.user, unidad_id, gestion_id)
    ):
        raise PermissionDenied('Unidad organizacional fuera de su alcance.')


class ScopePOAUMixin:
    scope_lookup = 'unidad_id'
    scope_target_field = 'unidad'

    def get_permissions(self):
        codigo = CAPACIDADES_POR_ACCION.get(
            self.action, 'sis_poa.poau.view',
        )
        return [CapacidadConScope(
            codigo, gestion_id_param='gestion_id', allow_empty_list=True,
        )]

    def get_queryset(self):
        queryset = super().get_queryset()
        unidades = _unidades_efectivas_o_none(self.request)
        if unidades is None:
            return queryset
        if not unidades:
            return queryset.none()
        return queryset.filter(**{f'{self.scope_lookup}__in': unidades})

    def _objetivo(self, serializer):
        return serializer.validated_data.get(
            self.scope_target_field,
            getattr(serializer.instance, self.scope_target_field, None),
        )

    def perform_create(self, serializer):
        _autorizar_objetivo(self.request, self._objetivo(serializer))
        serializer.save()

    def perform_update(self, serializer):
        _autorizar_objetivo(self.request, self._objetivo(serializer))
        serializer.save()


class POAUViewSet(ScopePOAUMixin, CandadoSisPoaMixin, viewsets.ModelViewSet):
    """POAU por unidad, acotado a la gestión habilitada (ADR-007)."""

    queryset = POAU.objects.select_related(
        'unidad', 'responsable',
    ).prefetch_related(
        Prefetch(
            'actividades',
            queryset=POAUActividad.objects.select_related('objeto_gasto').prefetch_related(
                Prefetch(
                    'ejecucion_fisica',
                    queryset=EjecucionFisica.objects.filter(
                        tipo_periodo='trimestral',
                    ),
                ),
            ),
        ),
    ).all()

    filter_backends = [DjangoFilterBackend]
    # 'gestion' salió del filtro libre: la pone el candado.
    filterset_fields = ['estado', 'unidad']
    search_fields = ['codigo', 'nombre', 'descripcion']
    ordering_fields = ['gestion', 'codigo', 'created_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return POAUListSerializer
        return POAUSerializer

    def _workflow_object(self, request, pk):
        gestion = gestion_del_candado(request)
        poau = get_object_or_404(self.queryset, pk=pk, gestion=gestion.anio)
        self.check_object_permissions(request, poau)
        return poau

    @action(detail=False, methods=['get'])
    def por_unidad(self, request):
        """Filtra POAUs por la unidad del usuario logueado.

        Soporta filtro explícito via ?unidad_id= o usa la primera
        asignación de unidad del usuario.
        """
        unidad_id = request.query_params.get('unidad_id')

        if not unidad_id:
            # Intentar obtener la unidad desde las asignaciones del usuario
            asignacion = request.user.asignaciones_unidad.filter(
                activo=True,
            ).select_related('unidad').first()
            if asignacion:
                unidad_id = asignacion.unidad_id
            else:
                return Response(
                    {'error': 'No se encontró una unidad asignada al usuario. '
                     'Especifique ?unidad_id='},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        qs = self.get_queryset().filter(unidad_id=unidad_id)
        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def enviar(self, request, pk=None):
        """Cambia estado a 'enviado'"""
        poau = self._workflow_object(request, pk)
        if poau.estado != 'borrador':
            return Response(
                {'error': f'No se puede enviar un POAU en estado "{poau.estado}"'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        poau.estado = 'enviado'
        poau.save(update_fields=['estado', 'updated_at'])
        return Response(POAUSerializer(poau).data)

    @action(detail=True, methods=['post'])
    def aprobar(self, request, pk=None):
        """Cambia estado a 'aprobado'"""
        poau = self._workflow_object(request, pk)
        if poau.estado != 'enviado':
            return Response(
                {'error': f'No se puede aprobar un POAU en estado "{poau.estado}"'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        poau.estado = 'aprobado'
        poau.save(update_fields=['estado', 'updated_at'])
        return Response(POAUSerializer(poau).data)

    @action(detail=True, methods=['post'])
    def rechazar(self, request, pk=None):
        """Cambia estado a 'rechazado'. Requiere observaciones en el body."""
        if 'observaciones' not in request.data:
            return Response(
                {'error': 'Se requiere el campo "observaciones" para rechazar'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        poau = self._workflow_object(request, pk)
        if poau.estado != 'enviado':
            return Response(
                {'error': f'No se puede rechazar un POAU en estado "{poau.estado}"'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        poau.estado = 'rechazado'
        poau.save(update_fields=['estado', 'updated_at'])
        return Response(POAUSerializer(poau).data)


class POAUActividadViewSet(
    ScopePOAUMixin, CandadoSisPoaMixin, viewsets.ModelViewSet,
):
    campo_gestion = 'poau__gestion'
    scope_lookup = 'poau__unidad_id'
    scope_target_field = 'poau'
    queryset = POAUActividad.objects.select_related(
        'poau', 'objeto_gasto',
    ).prefetch_related(
        Prefetch(
            'ejecucion_fisica',
            queryset=EjecucionFisica.objects.filter(
                tipo_periodo='trimestral',
            ),
        ),
    ).all()
    serializer_class = POAUActividadSerializer
    filterset_fields = ['poau', 'objeto_gasto']
    search_fields = ['codigo', 'nombre']
    ordering_fields = ['poau', 'codigo']


class EjecucionFisicaViewSet(
    ScopePOAUMixin, CandadoSisPoaMixin, viewsets.ModelViewSet,
):
    campo_gestion = 'actividad__poau__gestion'
    scope_lookup = 'actividad__poau__unidad_id'
    scope_target_field = 'actividad'
    queryset = EjecucionFisica.objects.select_related(
        'actividad__poau',
    ).all()
    serializer_class = EjecucionFisicaSerializer
    filterset_fields = ['actividad', 'tipo_periodo', 'periodo']
    search_fields = ['periodo', 'observaciones']
    ordering_fields = ['periodo', 'actividad']


class EjecucionFinancieraViewSet(
    ScopePOAUMixin, CandadoSisPoaMixin, viewsets.ModelViewSet,
):
    campo_gestion = 'actividad__poau__gestion'
    scope_lookup = 'actividad__poau__unidad_id'
    scope_target_field = 'actividad'
    queryset = EjecucionFinanciera.objects.select_related(
        'actividad__poau',
    ).all()
    serializer_class = EjecucionFinancieraSerializer
    filterset_fields = ['actividad', 'tipo_periodo', 'periodo']
    search_fields = ['periodo', 'observaciones']
    ordering_fields = ['periodo', 'actividad']
