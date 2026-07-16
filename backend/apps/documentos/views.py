from rest_framework import viewsets
from .models import DocumentoAdjunto
from .serializers import DocumentoAdjuntoSerializer


class DocumentoAdjuntoViewSet(viewsets.ModelViewSet):
    queryset = DocumentoAdjunto.objects.all()
    serializer_class = DocumentoAdjuntoSerializer
    filterset_fields = ['gestion', 'entidad', 'entidad_id', 'activo']
