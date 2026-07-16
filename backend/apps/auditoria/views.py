from rest_framework import viewsets
from .models import EventoAuditoria
from .serializers import EventoAuditoriaSerializer


class EventoAuditoriaViewSet(viewsets.ModelViewSet):
    queryset = EventoAuditoria.objects.all()
    serializer_class = EventoAuditoriaSerializer
    filterset_fields = ['accion', 'entidad', 'gestion', 'usuario']
    ordering_fields = ['creado_en']
    search_fields = ['entidad', 'entidad_id', 'resumen']
