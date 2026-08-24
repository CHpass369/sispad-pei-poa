"""F3b1: lectura, edición y estado de usuarios en API administrativa V2."""

import logging

from django.db import transaction
from django.db.models import Prefetch, Q
from rest_framework import generics, status
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

from apps.accounts.models import (
    AlcanceOrganizacional,
    Capacidad,
    Rol,
    Usuario,
)
from apps.accounts.permissions import TieneCapacidad
from apps.accounts.serializers import (
    UsuarioAdminFilterSerializer,
    UsuarioAdminReadSerializer,
    UsuarioAdminUpdateSerializer,
)
from apps.accounts.services import (
    limitar_usuarios_administrables,
    usuarios_con_sistema,
)

logger = logging.getLogger(__name__)


def _queryset_usuario_admin():
    capacidades = Prefetch(
        'capacidades',
        queryset=Capacidad.objects.filter(activo=True).order_by('codigo'),
        to_attr='capacidades_activas',
    )
    roles = Prefetch(
        'roles',
        queryset=(
            Rol.objects.filter(activo=True)
            .prefetch_related(capacidades)
            .order_by('orden', 'nombre')
        ),
        to_attr='roles_admin',
    )
    alcances = Prefetch(
        'alcances_organizacionales',
        queryset=(
            AlcanceOrganizacional.objects.filter(activo=True)
            .select_related('rol', 'unidad', 'fiscal_year')
            .prefetch_related(
                Prefetch(
                    'rol__capacidades',
                    queryset=Capacidad.objects.filter(activo=True),
                    to_attr='capacidades_activas',
                ),
            )
            .order_by('unidad__codigo', 'rol__orden')
        ),
        to_attr='alcances_admin',
    )
    return Usuario.objects.prefetch_related(roles, alcances)


def _usuarios_visibles(administrador):
    return limitar_usuarios_administrables(
        _queryset_usuario_admin(), administrador,
    )


class UsuarioAdminListView(generics.ListAPIView):
    serializer_class = UsuarioAdminReadSerializer
    authentication_classes = [JWTAuthentication]
    pagination_class = PageNumberPagination

    def get_permissions(self):
        return [TieneCapacidad('accounts.usuario.view')]

    def get_queryset(self):
        filtros = UsuarioAdminFilterSerializer(data=self.request.query_params)
        filtros.is_valid(raise_exception=True)
        data = filtros.validated_data
        queryset = _usuarios_visibles(self.request.user)

        if search := data.get('search'):
            queryset = queryset.filter(
                Q(first_name__icontains=search)
                | Q(last_name__icontains=search)
                | Q(email__icontains=search)
                | Q(cargo__icontains=search)
            )
        if unidad := data.get('organizational_unit'):
            queryset = queryset.filter(
                alcances_organizacionales__unidad_id=unidad,
            )
        if role := data.get('role'):
            queryset = queryset.filter(roles__codigo=role)
        if sistema := data.get('system'):
            queryset = usuarios_con_sistema(queryset, sistema)
        if estado := data.get('state'):
            queryset = queryset.filter(estado=estado)
        return queryset.distinct().order_by('last_name', 'first_name', 'id')


class UsuarioAdminDetailView(generics.RetrieveUpdateAPIView):
    authentication_classes = [JWTAuthentication]
    http_method_names = ['get', 'patch', 'head', 'options']

    def get_permissions(self):
        capacidad = (
            'accounts.usuario.edit'
            if self.request.method == 'PATCH'
            else 'accounts.usuario.view'
        )
        return [TieneCapacidad(capacidad)]

    def get_queryset(self):
        return _usuarios_visibles(self.request.user)

    def get_serializer_class(self):
        if self.request.method == 'PATCH':
            return UsuarioAdminUpdateSerializer
        return UsuarioAdminReadSerializer

    def patch(self, request, *args, **kwargs):
        usuario = self.get_object()
        serializer = UsuarioAdminUpdateSerializer(
            usuario, data=request.data, partial=True,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        actualizado = _usuarios_visibles(request.user).get(pk=usuario.pk)
        return Response(UsuarioAdminReadSerializer(actualizado).data)


class _CambiarEstadoUsuarioView(APIView):
    authentication_classes = [JWTAuthentication]
    estado = None

    def get_permissions(self):
        return [TieneCapacidad('accounts.usuario.activate')]

    @transaction.atomic
    def post(self, request, pk):
        try:
            usuario = (
                _usuarios_visibles(request.user)
                .select_for_update()
                .get(pk=pk)
            )
        except (Usuario.DoesNotExist, ValueError):
            return Response(
                {'error': 'Usuario no encontrado.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        if self.estado == Usuario.ESTADO_INACTIVO and usuario.pk == request.user.pk:
            return Response(
                {'error': 'No puede desactivar su propia cuenta.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        activo = self.estado == Usuario.ESTADO_ACTIVO
        usuario.estado = self.estado
        usuario.activo = activo
        usuario.is_active = activo
        usuario.save(update_fields=['estado', 'activo', 'is_active'])
        logger.info(
            'Estado de usuario %s cambiado a %s por %s',
            usuario.email, self.estado, request.user.email,
        )
        return Response(UsuarioAdminReadSerializer(usuario).data)


class ActivarUsuarioView(_CambiarEstadoUsuarioView):
    estado = Usuario.ESTADO_ACTIVO


class DesactivarUsuarioView(_CambiarEstadoUsuarioView):
    estado = Usuario.ESTADO_INACTIVO
