from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import TipoUnidad, UnidadOrganizacional, DireccionAdministrativa, UnidadEjecutora, AsignacionUsuarioUnidad
from .serializers import (
    TipoUnidadSerializer, UnidadOrganizacionalSerializer,
    UnidadOrganizacionalTreeSerializer, DireccionAdministrativaSerializer,
    UnidadEjecutoraSerializer, AsignacionUsuarioUnidadSerializer
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
    queryset = AsignacionUsuarioUnidad.objects.all()
    serializer_class = AsignacionUsuarioUnidadSerializer
    filterset_fields = ['usuario', 'unidad', 'activo']

    def get_queryset(self):
        qs = super().get_queryset()
        gestion = self.request.query_params.get('gestion')
        if gestion:
            qs = qs.filter(gestion__anio=gestion)
        return qs
