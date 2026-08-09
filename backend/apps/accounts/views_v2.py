"""Vistas V2 de identidad (namespace /api/v2/me/)."""
from rest_framework import viewsets, permissions
from rest_framework.response import Response


class MeViewSet(viewsets.ViewSet):
    """Identidad del usuario autenticado y sus capacidades.

    Contrato V2 (ADR-002): el frontend construye menú y acciones a partir de
    las capacidades; los roles no se codifican en componentes (ADR-003).
    Las capacidades se completan en WP-03 (IAM).
    """

    permission_classes = [permissions.IsAuthenticated]

    def list(self, request):
        user = request.user
        return Response({
            'id': str(user.id),
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'roles': [
                {'codigo': r.codigo, 'nombre': r.nombre}
                for r in user.roles.filter(activo=True).order_by('orden')
            ],
            'capabilities': [],
            'alcances': [],
        })

    def retrieve(self, request, pk=None):
        return self.list(request)
