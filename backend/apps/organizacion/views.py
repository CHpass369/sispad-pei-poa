from django.db import transaction
from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from apps.accounts.permissions import TieneCapacidad

from .models import TipoUnidad, UnidadOrganizacional, DireccionAdministrativa, UnidadEjecutora, AsignacionUsuarioUnidad
from .serializers import (
    TipoUnidadSerializer, UnidadOrganizacionalSerializer,
    UnidadOrganizacionalTreeSerializer, DireccionAdministrativaSerializer,
    UnidadEjecutoraSerializer, AsignacionUsuarioUnidadSerializer
)
from .services import (
    FormulatorAssignmentConflict,
    synchronize_formulator_scopes_from_legacy,
)


class TipoUnidadViewSet(viewsets.ModelViewSet):
    queryset = TipoUnidad.objects.all()
    serializer_class = TipoUnidadSerializer
    search_fields = ['codigo', 'nombre']


class UnidadOrganizacionalViewSet(viewsets.ModelViewSet):
    queryset = UnidadOrganizacional.objects.all()
    serializer_class = UnidadOrganizacionalSerializer
    search_fields = ['codigo', 'nombre', 'sigla']
    filterset_fields = ['tipo', 'activo', 'padre']

    def get_queryset(self):
        """Contrato PIP-DB-002: `?gestion=<año>` sigue filtrando por año."""
        qs = super().get_queryset()
        gestion = self.request.query_params.get('gestion')
        if gestion:
            qs = qs.filter(gestion__anio=gestion)
        return qs

    @action(detail=False, methods=['get'])
    def arbol(self, request):
        gestion = request.query_params.get('gestion')
        queryset = self.get_queryset().filter(padre__isnull=True, activo=True)
        if gestion:
            queryset = queryset.filter(gestion__anio=gestion)
        serializer = UnidadOrganizacionalTreeSerializer(queryset, many=True)
        return Response(serializer.data)


class DireccionAdministrativaViewSet(viewsets.ModelViewSet):
    queryset = DireccionAdministrativa.objects.all()
    serializer_class = DireccionAdministrativaSerializer
    search_fields = ['codigo', 'nombre']
    filterset_fields = ['activo']

    def get_queryset(self):
        qs = super().get_queryset()
        gestion = self.request.query_params.get('gestion')
        if gestion:
            qs = qs.filter(gestion__anio=gestion)
        return qs


class UnidadEjecutoraViewSet(viewsets.ModelViewSet):
    queryset = UnidadEjecutora.objects.all()
    serializer_class = UnidadEjecutoraSerializer
    search_fields = ['codigo', 'nombre']
    filterset_fields = ['da', 'activo']

    def get_queryset(self):
        qs = super().get_queryset()
        gestion = self.request.query_params.get('gestion')
        if gestion:
            qs = qs.filter(gestion__anio=gestion)
        return qs


class AsignacionUsuarioUnidadViewSet(viewsets.ModelViewSet):
    READ_ACTIONS = frozenset({'list', 'retrieve'})
    READ_CAPABILITY = 'accounts.alcance.view'
    MUTATION_CAPABILITY = 'accounts.alcance.assign'
    queryset = AsignacionUsuarioUnidad.objects.all()
    serializer_class = AsignacionUsuarioUnidadSerializer
    filterset_fields = ['usuario', 'unidad', 'activo']

    def get_permissions(self):
        capability = (
            self.READ_CAPABILITY
            if self.action in self.READ_ACTIONS
            else self.MUTATION_CAPABILITY
        )
        return [permissions.IsAuthenticated(), TieneCapacidad(capability)]

    def get_queryset(self):
        qs = super().get_queryset()
        gestion = self.request.query_params.get('gestion')
        if gestion:
            qs = qs.filter(gestion__anio=gestion)
        return qs

    @staticmethod
    def _synchronize(pairs):
        try:
            synchronize_formulator_scopes_from_legacy(pairs)
        except FormulatorAssignmentConflict as exc:
            raise ValidationError(str(exc)) from exc

    @transaction.atomic
    def perform_create(self, serializer):
        assignment = serializer.save()
        self._synchronize({(assignment.usuario_id, assignment.gestion_id)})

    @transaction.atomic
    def perform_update(self, serializer):
        previous = (serializer.instance.usuario_id, serializer.instance.gestion_id)
        assignment = serializer.save()
        self._synchronize({
            previous,
            (assignment.usuario_id, assignment.gestion_id),
        })

    @transaction.atomic
    def perform_destroy(self, instance):
        pair = (instance.usuario_id, instance.gestion_id)
        instance.delete()
        self._synchronize({pair})
