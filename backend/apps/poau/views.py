from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Prefetch

from .models import POAU, POAUActividad, EjecucionFisica, EjecucionFinanciera
from .serializers import (
    POAUSerializer, POAUListSerializer, POAUActividadSerializer,
    EjecucionFisicaSerializer, EjecucionFinancieraSerializer,
)


class POAUViewSet(viewsets.ModelViewSet):
    queryset = POAU.objects.select_related(
        'unidad', 'producto_territorial', 'responsable',
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
    filterset_fields = ['gestion', 'estado', 'unidad']
    search_fields = ['codigo', 'nombre', 'descripcion']
    ordering_fields = ['gestion', 'codigo', 'created_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return POAUListSerializer
        return POAUSerializer

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
        poau = self.get_object()
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
        poau = self.get_object()
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
        poau = self.get_object()
        if poau.estado != 'enviado':
            return Response(
                {'error': f'No se puede rechazar un POAU en estado "{poau.estado}"'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        poau.estado = 'rechazado'
        poau.save(update_fields=['estado', 'updated_at'])
        return Response(POAUSerializer(poau).data)


class POAUActividadViewSet(viewsets.ModelViewSet):
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


class EjecucionFisicaViewSet(viewsets.ModelViewSet):
    queryset = EjecucionFisica.objects.select_related(
        'actividad__poau',
    ).all()
    serializer_class = EjecucionFisicaSerializer
    filterset_fields = ['actividad', 'tipo_periodo', 'periodo']
    search_fields = ['periodo', 'observaciones']
    ordering_fields = ['periodo', 'actividad']


class EjecucionFinancieraViewSet(viewsets.ModelViewSet):
    queryset = EjecucionFinanciera.objects.select_related(
        'actividad__poau',
    ).all()
    serializer_class = EjecucionFinancieraSerializer
    filterset_fields = ['actividad', 'tipo_periodo', 'periodo']
    search_fields = ['periodo', 'observaciones']
    ordering_fields = ['periodo', 'actividad']
