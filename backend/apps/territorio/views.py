from django.db.models import Prefetch
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.gestion.candado import anio_habilitado

from .models import (
    DirigenteTerritorial, Distrito, LocalizacionTerritorial, UnidadTerritorial,
    clave_organizacion,
)
from .serializers import (
    DirigenteTerritorialSerializer, DistritoSerializer,
    LocalizacionTerritorialSerializer, OrganizacionDominioSerializer,
    UnidadTerritorialSerializer,
)


class DistritoViewSet(viewsets.ModelViewSet):
    queryset = Distrito.objects.all()
    serializer_class = DistritoSerializer
    search_fields = ['codigo', 'nombre']


class UnidadTerritorialViewSet(viewsets.ModelViewSet):
    queryset = UnidadTerritorial.objects.all()
    serializer_class = UnidadTerritorialSerializer
    filterset_fields = ['distrito', 'tipo']
    search_fields = ['codigo', 'nombre']

    @action(detail=False, methods=['get'])
    def dominio(self, request):
        """Padrón de organizaciones para llenar los campos del acta.

        Devuelve la lista completa del distrito —el más grande tiene 79— con su
        dirigente vigente pegado. Sin paginar: el formulario la necesita entera
        para resolver la selección sin ir y volver al servidor.

        `q` acota por NOMBRE DE ORGANIZACIÓN, palabra por palabra. No busca por
        dirigente: el formulario filtra en memoria y ahí sí mira los dos.
        """
        gestion = request.query_params.get('gestion') or anio_habilitado()
        dirigentes = DirigenteTerritorial.objects.filter(vigente=True)
        if gestion:
            dirigentes = dirigentes.filter(gestion=gestion)

        consulta = (UnidadTerritorial.objects
                    .filter(activa=True)
                    .select_related('distrito')
                    .prefetch_related(Prefetch(
                        'dirigentes',
                        queryset=dirigentes.order_by('-gestion', 'cargo'),
                        to_attr='dirigentes_vigentes')))

        distrito = request.query_params.get('distrito')
        if distrito:
            consulta = consulta.filter(distrito_id=distrito)
        tipo = request.query_params.get('tipo')
        if tipo:
            consulta = consulta.filter(tipo=tipo)
        texto = clave_organizacion(request.query_params.get('q', ''))
        for palabra in texto.split():
            consulta = consulta.filter(nombre_busqueda__contains=palabra)

        datos = OrganizacionDominioSerializer(consulta.order_by('nombre'),
                                              many=True).data
        return Response({'gestion': gestion, 'total': len(datos),
                         'resultados': datos})


class DirigenteTerritorialViewSet(viewsets.ModelViewSet):
    queryset = (DirigenteTerritorial.objects
                .select_related('unidad', 'unidad__distrito'))
    serializer_class = DirigenteTerritorialSerializer
    filterset_fields = ['unidad', 'gestion', 'vigente']
    search_fields = ['nombre', 'cargo']


class LocalizacionTerritorialViewSet(viewsets.ModelViewSet):
    queryset = LocalizacionTerritorial.objects.all()
    serializer_class = LocalizacionTerritorialSerializer
    filterset_fields = ['gestion', 'distrito', 'activo']
