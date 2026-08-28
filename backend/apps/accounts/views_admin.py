"""F3b1/F3b2a/F3b2b: administración IAM en API V2."""

import logging

from django.db import transaction
from django.db.models import Prefetch, Q
from django.http import Http404
from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied
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
    AsignacionCapacidadesRolSerializer,
    AsignacionesUsuarioSerializer,
    CapacidadAdminFilterSerializer,
    CapacidadAdminReadSerializer,
    PreviewAccessRequestSerializer,
    PreviewAccessResponseSerializer,
    RolAdminCreateSerializer,
    RolAdminFilterSerializer,
    RolAdminReadSerializer,
    RolAdminUpdateSerializer,
    UsuarioAdminFilterSerializer,
    UsuarioAdminReadSerializer,
    UsuarioAdminUpdateSerializer,
)
from apps.accounts.services import (
    es_super_admin,
    limitar_objetivos_asignaciones,
    limitar_roles_administrables,
    limitar_usuarios_administrables,
    puede_administrar_asignacion_rol,
    roles_con_sistema,
    usuarios_con_sistema,
)
from apps.accounts.services_scope import evaluar_acceso_efectivo
from apps.organizacion.services import (
    FORMULATOR_ROLE_CODE,
    synchronize_legacy_from_formulator_scopes,
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


def _objetivos_asignaciones(administrador):
    return limitar_objetivos_asignaciones(
        _queryset_usuario_admin(), administrador,
    )


def _roles_reemplazables(usuario, administrador):
    capacidades = Prefetch(
        'capacidades', queryset=Capacidad.objects.order_by('codigo'),
        to_attr='capacidades_admin',
    )
    roles = Rol.objects.filter(
        Q(usuarios=usuario)
        | Q(alcances__usuario=usuario, alcances__activo=True),
    ).prefetch_related(capacidades).distinct()
    return roles, {
        rol.pk for rol in roles
        if puede_administrar_asignacion_rol(administrador, rol)
    }


class AsignacionesUsuarioView(APIView):
    authentication_classes = [JWTAuthentication]

    def get_permissions(self):
        capacidad = (
            'accounts.alcance.assign'
            if self.request.method == 'PUT'
            else 'accounts.alcance.view'
        )
        return [TieneCapacidad(capacidad)]

    @staticmethod
    def _usuario_no_encontrado():
        return Response(
            {'error': 'Usuario no encontrado.'},
            status=status.HTTP_404_NOT_FOUND,
        )

    @staticmethod
    def _rechazar_pendiente(usuario):
        if usuario.estado != Usuario.ESTADO_PENDIENTE:
            return None
        return Response(
            {'error': 'Las asignaciones requieren un usuario aprobado.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    def get(self, request, pk):
        try:
            usuario = _objetivos_asignaciones(request.user).get(pk=pk)
        except (Usuario.DoesNotExist, ValueError):
            return self._usuario_no_encontrado()
        if respuesta := self._rechazar_pendiente(usuario):
            return respuesta
        return Response(UsuarioAdminReadSerializer(usuario).data)

    @transaction.atomic
    def put(self, request, pk):
        try:
            usuario = (
                _objetivos_asignaciones(request.user)
                .select_for_update()
                .get(pk=pk)
            )
        except (Usuario.DoesNotExist, ValueError):
            return self._usuario_no_encontrado()
        if respuesta := self._rechazar_pendiente(usuario):
            return respuesta
        if usuario.pk == request.user.pk and not es_super_admin(request.user):
            raise PermissionDenied(
                'No puede modificar sus propias asignaciones.',
            )

        serializer = AsignacionesUsuarioSerializer(
            data=request.data,
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        asignaciones = serializer.validated_data['assignments']

        roles_actuales, roles_reemplazables = _roles_reemplazables(
            usuario, request.user,
        )
        formulator_years = set(
            AlcanceOrganizacional.objects.filter(
                usuario=usuario,
                activo=True,
                rol_id__in=roles_reemplazables,
                rol__codigo=FORMULATOR_ROLE_CODE,
            ).values_list('fiscal_year_id', flat=True)
        )
        formulator_years.update(
            assignment['fiscal_year'].pk
            for assignment in asignaciones
            if assignment['rol'].codigo == FORMULATOR_ROLE_CODE
        )
        if any(
            rol.pk in roles_reemplazables
            and rol.codigo == FORMULATOR_ROLE_CODE
            for rol in roles_actuales
        ):
            formulator_years.update(
                usuario.asignaciones_unidad.filter(activo=True).values_list(
                    'gestion_id', flat=True,
                )
            )

        AlcanceOrganizacional.objects.filter(
            usuario=usuario,
            activo=True,
            rol_id__in=roles_reemplazables,
        ).delete()
        AlcanceOrganizacional.objects.bulk_create([
            AlcanceOrganizacional(
                usuario=usuario,
                rol=asignacion['rol'],
                unidad=asignacion['unidad'],
                scope_type=asignacion['scope_type'],
                fiscal_year=asignacion['fiscal_year'],
                activo=True,
            )
            for asignacion in asignaciones
        ])

        roles_preservados = set(
            usuario.roles.exclude(pk__in=roles_reemplazables)
            .values_list('pk', flat=True)
        )
        roles_nuevos = {asignacion['rol'].pk for asignacion in asignaciones}
        usuario.roles.set(roles_preservados | roles_nuevos)
        synchronize_legacy_from_formulator_scopes(usuario, formulator_years)

        actualizado = _queryset_usuario_admin().get(pk=usuario.pk)
        logger.info(
            'Asignaciones de usuario %s reemplazadas por %s',
            usuario.email,
            request.user.email,
        )
        return Response(UsuarioAdminReadSerializer(actualizado).data)


class PreviewAccessView(APIView):
    authentication_classes = [JWTAuthentication]

    def get_permissions(self):
        return [TieneCapacidad('accounts.alcance.assign')]

    def get(self, request):
        serializer = PreviewAccessRequestSerializer(
            data=request.query_params, context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        try:
            usuario = _objetivos_asignaciones(request.user).get(pk=data['user_id'])
        except Usuario.DoesNotExist:
            return AsignacionesUsuarioView._usuario_no_encontrado()
        if respuesta := AsignacionesUsuarioView._rechazar_pendiente(usuario):
            return respuesta

        assignments = data['assignments']
        reemplazables = ()
        if assignments:
            _, reemplazables = _roles_reemplazables(usuario, request.user)
        resultado = evaluar_acceso_efectivo(
            usuario,
            assignments if assignments else None,
            reemplazables,
        )
        return Response(PreviewAccessResponseSerializer(resultado).data)


def _queryset_rol_admin():
    capacidades = Prefetch(
        'capacidades',
        queryset=Capacidad.objects.order_by('codigo'),
        to_attr='capacidades_admin',
    )
    return Rol.objects.prefetch_related(capacidades)


def _filtros_roles(request):
    filtros = RolAdminFilterSerializer(data=request.query_params)
    filtros.is_valid(raise_exception=True)
    data = filtros.validated_data
    if data['include_deprecated'] and not request.user.is_superuser:
        raise PermissionDenied(
            'Solo un superusuario puede incluir roles deprecated.',
        )
    return data


def _roles_visibles(request):
    data = _filtros_roles(request)
    queryset = limitar_roles_administrables(
        _queryset_rol_admin(), request.user,
    )
    if not data['include_deprecated']:
        queryset = queryset.filter(deprecated=False)
    if search := data.get('search'):
        queryset = queryset.filter(
            Q(codigo__icontains=search)
            | Q(nombre__icontains=search)
            | Q(descripcion__icontains=search)
        )
    if sistema := data.get('system'):
        queryset = roles_con_sistema(queryset, sistema)
    if 'active' in request.query_params:
        queryset = queryset.filter(activo=data['active'])
    return queryset.order_by('orden', 'nombre', 'id')


class RolAdminListCreateView(generics.ListCreateAPIView):
    authentication_classes = [JWTAuthentication]
    pagination_class = PageNumberPagination

    def get_permissions(self):
        capacidad = (
            'accounts.rol.create'
            if self.request.method == 'POST'
            else 'accounts.rol.view'
        )
        return [TieneCapacidad(capacidad)]

    def get_queryset(self):
        return _roles_visibles(self.request)

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return RolAdminCreateSerializer
        return RolAdminReadSerializer

    def create(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            raise PermissionDenied(
                'Solo un superusuario puede crear roles personalizados.',
            )
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        rol = serializer.save()
        rol = _queryset_rol_admin().get(pk=rol.pk)
        return Response(
            RolAdminReadSerializer(rol).data,
            status=status.HTTP_201_CREATED,
        )


class RolAdminDetailView(generics.RetrieveUpdateDestroyAPIView):
    authentication_classes = [JWTAuthentication]
    http_method_names = ['get', 'patch', 'delete', 'head', 'options']

    def get_permissions(self):
        capacidad = (
            'accounts.rol.edit'
            if self.request.method in {'PATCH', 'DELETE'}
            else 'accounts.rol.view'
        )
        return [TieneCapacidad(capacidad)]

    def get_queryset(self):
        return _roles_visibles(self.request)

    def get_serializer_class(self):
        if self.request.method == 'PATCH':
            return RolAdminUpdateSerializer
        return RolAdminReadSerializer

    def patch(self, request, *args, **kwargs):
        rol = self.get_object()
        serializer = self.get_serializer(
            rol, data=request.data, partial=True,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        actualizado = _queryset_rol_admin().get(pk=rol.pk)
        return Response(RolAdminReadSerializer(actualizado).data)

    @transaction.atomic
    def delete(self, request, *args, **kwargs):
        visible = self.get_object()
        try:
            rol = Rol.objects.select_for_update().get(pk=visible.pk)
        except Rol.DoesNotExist as exc:
            raise Http404 from exc
        references = {
            'users': rol.usuarios.count(),
            'organizational_scopes': rol.alcances.count(),
        }
        if any(references.values()):
            return Response(
                {
                    'code': 'role_in_use',
                    'error': (
                        'El rol está asignado o conserva alcances organizacionales. '
                        'Retire primero las asignaciones de usuarios y alcances.'
                    ),
                    'references': references,
                },
                status=status.HTTP_409_CONFLICT,
            )
        rol.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class AsignarCapacidadesRolView(APIView):
    authentication_classes = [JWTAuthentication]

    def get_permissions(self):
        return [TieneCapacidad('accounts.capacidad.assign')]

    @transaction.atomic
    def put(self, request, pk):
        try:
            roles_visibles = limitar_roles_administrables(
                Rol.objects.filter(deprecated=False), request.user,
            )
            rol = roles_visibles.select_for_update().get(pk=pk)
        except (Rol.DoesNotExist, ValueError):
            return Response(
                {'error': 'Rol no encontrado.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = AsignacionCapacidadesRolSerializer(
            data=request.data, context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        rol.capacidades.set(serializer.validated_data['capability_codes'])
        actualizado = _queryset_rol_admin().get(pk=rol.pk)
        return Response(RolAdminReadSerializer(actualizado).data)


class CapacidadAdminListView(generics.ListAPIView):
    serializer_class = CapacidadAdminReadSerializer
    authentication_classes = [JWTAuthentication]
    pagination_class = PageNumberPagination

    def get_permissions(self):
        return [TieneCapacidad('accounts.capacidad.view')]

    def get_queryset(self):
        filtros = CapacidadAdminFilterSerializer(data=self.request.query_params)
        filtros.is_valid(raise_exception=True)
        data = filtros.validated_data
        queryset = Capacidad.objects.exclude(
            Q(codigo__istartswith='sis_pro.')
            | Q(codigo__istartswith='sis-pro.'),
        )
        if search := data.get('search'):
            queryset = queryset.filter(
                Q(codigo__icontains=search)
                | Q(nombre__icontains=search)
                | Q(descripcion__icontains=search)
            )
        if sistema := data.get('system'):
            queryset = queryset.filter(codigo__startswith=f'{sistema}.')
        if 'active' in self.request.query_params:
            queryset = queryset.filter(activo=data['active'])
        return queryset.order_by('codigo', 'id')
