from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from .models import SectorPAD
from .serializers import SectorPADSerializer


class SectorPADViewSet(viewsets.ModelViewSet):
    """Catálogo de sectores del PAD (solo lectura efectiva en la práctica)."""

    queryset = SectorPAD.objects.all()
    serializer_class = SectorPADSerializer
    permission_classes = [IsAuthenticated]
