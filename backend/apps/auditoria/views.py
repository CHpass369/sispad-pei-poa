from rest_framework import viewsets

from apps.core.pagination import AuditoriaDualPagination

from .models import EventoAuditoria
from .serializers import EventoAuditoriaSerializer


class EventoAuditoriaViewSet(viewsets.ModelViewSet):
    queryset = EventoAuditoria.objects.all()
    serializer_class = EventoAuditoriaSerializer
    pagination_class = AuditoriaDualPagination
    filterset_fields = ['accion', 'entidad', 'gestion', 'usuario']
    ordering_fields = ['creado_en']
    ordering = ['-creado_en']
    search_fields = ['entidad', 'entidad_id', 'resumen']
