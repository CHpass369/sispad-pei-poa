"""Vistas V2 de identidad (namespace /api/v2/me/)."""
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.accounts.permissions import listar_capacidades


def _serializar_me(user):
    return {
        'id': str(user.id),
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'roles': [
            {'codigo': r.codigo, 'nombre': r.nombre}
            for r in user.roles.filter(activo=True).order_by('orden')
        ],
    }


class MeViewSet(viewsets.ViewSet):
    """Identidad del usuario autenticado, capacidades y alcances (ADR-003).

    Contrato: el frontend construye menú y acciones a partir de
    `/api/v2/me/capabilities`; los roles no se codifican en componentes.
    """

    permission_classes = [permissions.IsAuthenticated]

    def list(self, request):
        user = request.user
        data = _serializar_me(user)
        data['capabilities'] = listar_capacidades(user)
        data['alcances'] = _alcances(user)
        return Response(data)

    def retrieve(self, request, pk=None):
        return self.list(request)

    @action(detail=False, methods=['get'])
    def capabilities(self, request):
        """Capacidades y alcances efectivos (menú/acciones del frontend)."""
        user = request.user
        return Response({
            'usuario': {
                'id': str(user.id),
                'email': user.email,
            },
            'roles': [
                r.codigo
                for r in user.roles.filter(activo=True).order_by('orden')
            ],
            'capabilities': listar_capacidades(user),
            'alcances': _alcances(user),
        })


def _alcances(user):
    alcances = user.alcances_organizacionales.filter(activo=True)
    return [
        {
            'tipo': 'organizacional',
            'unidad_id': str(a.unidad_id),
            'unidad_nombre': a.unidad.nombre,
            'sigla': a.unidad.sigla,
            'vigente_desde': str(a.vigente_desde) if a.vigente_desde else None,
            'vigente_hasta': str(a.vigente_hasta) if a.vigente_hasta else None,
        }
        for a in alcances.select_related('unidad')
    ]
