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
    filterset_fields = ['gestion', 'tipo', 'activo', 'padre']

    @action(detail=False, methods=['get'])
    def arbol(self, request):
        gestion = request.query_params.get('gestion')
        queryset = self.get_queryset().filter(padre__isnull=True, activo=True)
        if gestion:
            queryset = queryset.filter(gestion=gestion)
        serializer = UnidadOrganizacionalTreeSerializer(queryset, many=True)
        return Response(serializer.data)


class DireccionAdministrativaViewSet(viewsets.ModelViewSet):
    queryset = DireccionAdministrativa.objects.all()
    serializer_class = DireccionAdministrativaSerializer
    search_fields = ['codigo', 'nombre']
    filterset_fields = ['gestion', 'activo']


class UnidadEjecutoraViewSet(viewsets.ModelViewSet):
    queryset = UnidadEjecutora.objects.all()
    serializer_class = UnidadEjecutoraSerializer
    search_fields = ['codigo', 'nombre']
    filterset_fields = ['gestion', 'da', 'activo']


class AsignacionUsuarioUnidadViewSet(viewsets.ModelViewSet):
    queryset = AsignacionUsuarioUnidad.objects.all()
    serializer_class = AsignacionUsuarioUnidadSerializer
    filterset_fields = ['usuario', 'unidad', 'gestion', 'activo']
