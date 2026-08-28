"""F3a: registro público de usuarios y aprobación administrativa (spec #17/#18).

Endpoints (namespace /api/v2/, ver apps.accounts.urls_v2):

- POST /api/v2/auth/register/          público; crea Usuario PENDIENTE.
- POST /api/v2/admin/users/{id}/approve/  capacidad accounts.solicitud.approve.
- GET  /api/v2/admin/solicitudes/      capacidad accounts.solicitud.view.

Decisiones:

- El registro NO inicia sesión ni devuelve token: el usuario espera la
  aprobación y luego hace login normal (spec #17).
- Un usuario autenticado no puede usar el registro público (400).
- La UO pedida en el registro se persiste como alcance-trazo
  (`AlcanceOrganizacional` con rol=None, activo=False): nunca es vigente
  (ScopeResolver filtra activo=True y exige usuario.activo) y sirve para
  mostrar `unidad_solicitada` en el listado de solicitudes.
- `es_encargado_unidad` es una DECLARACIÓN, no una concesión: este endpoint es
  público, así que marcar la casilla no otorga `sis_poa.poau.approve`. Se
  guarda en `Usuario.solicita_encargado_unidad` y solo alimenta el
  `rol_sugerido` que el administrador ve (y confirma) al aprobar.
- Un administrador no puede aprobarse a sí mismo (403).
- Los roles base usan el scope normativo compartido; los roles personalizados
  usan el `scope_type` del payload.
"""
import logging

from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Q
from rest_framework import generics, permissions, status
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

from apps.accounts.models import AlcanceOrganizacional, Rol
from apps.accounts.permissions import TieneCapacidad
from apps.accounts.services import (
    SCOPES_FIJOS_ROLES_SISTEMA,
    SISTEMAS_POR_ROL,
    puede_administrar_asignacion_rol,
    puede_administrar_sistema,
    unidades_organizacionales_disponibles_registro,
)
from apps.accounts.serializers import (
    AprobacionSerializer,
    RegistroPublicoSerializer,
    SolicitudSerializer,
    UnidadOrganizacionalPublicaSerializer,
    validar_gestion_fiscal_asignacion,
)
from apps.accounts.views import LoginThrottle
from apps.gestion.models import GestionFiscal
from apps.organizacion.models import UnidadOrganizacional

logger = logging.getLogger(__name__)
Usuario = get_user_model()

class RegistroPublicoView(APIView):
    """POST /api/v2/auth/register/ — alta pública, queda PENDIENTE."""

    permission_classes = [permissions.AllowAny]
    throttle_classes = [LoginThrottle]

    @transaction.atomic
    def post(self, request):
        if request.user and request.user.is_authenticated:
            return Response(
                {'error': 'Ya tiene una sesión activa. '
                          'Cierre sesión para registrar una nueva cuenta.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = RegistroPublicoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        usuario = Usuario(
            email=data['email'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            cargo=data.get('cargo', ''),
            solicita_encargado_unidad=data.get('es_encargado_unidad', False),
            estado=Usuario.ESTADO_PENDIENTE,  # save() fuerza activo=False
            is_active=False,
            is_staff=False,
            is_superuser=False,
        )
        usuario.set_password(data['password'])
        usuario.save()

        # Trazo de la UO solicitada: inactivo y sin rol → nunca vigente.
        unidad_solicitada = UnidadOrganizacional.objects.only(
            'gestion_id',
        ).get(pk=data['unidad_organizacional_id'])
        AlcanceOrganizacional.objects.create(
            usuario=usuario,
            unidad=unidad_solicitada,
            rol=None,
            scope_type=AlcanceOrganizacional.SCOPE_SELF,
            fiscal_year_id=unidad_solicitada.gestion_id,
            activo=False,
        )
        logger.info('Registro público recibido: %s', usuario.email)
        return Response(
            {'detail': 'Registro recibido. '
                       'Un administrador revisará su solicitud.'},
            status=status.HTTP_201_CREATED,
        )


class UnidadesOrganizacionalesPublicasView(generics.ListAPIView):
    """GET público con los únicos datos de UO necesarios para registrarse."""

    permission_classes = [permissions.AllowAny]
    serializer_class = UnidadOrganizacionalPublicaSerializer
    pagination_class = None

    def get_queryset(self):
        queryset = unidades_organizacionales_disponibles_registro()
        search = self.request.query_params.get('search', '').strip()
        if search:
            queryset = queryset.filter(
                Q(codigo__icontains=search)
                | Q(nombre__icontains=search)
                | Q(sigla__icontains=search)
            )
        return queryset.order_by('nombre', 'codigo')


class AprobarUsuarioView(APIView):
    """POST /api/v2/admin/users/{id}/approve/ — PENDIENTE → ACTIVO (#18)."""

    authentication_classes = [JWTAuthentication]

    def get_permissions(self):
        # Patrón del proyecto (gestion/budget): instancias desde
        # get_permissions, no clases en permission_classes.
        return [TieneCapacidad('accounts.solicitud.approve')]

    @transaction.atomic
    def post(self, request, pk):
        try:
            usuario = Usuario.objects.select_for_update().get(pk=pk)
        except (Usuario.DoesNotExist, ValueError):
            return Response(
                {'error': 'Usuario no encontrado.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        if usuario.pk == request.user.pk:
            return Response(
                {'error': 'No puede aprobar su propia solicitud.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        if usuario.estado != Usuario.ESTADO_PENDIENTE:
            return Response(
                {'error': 'Solo se pueden aprobar solicitudes pendientes.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = AprobacionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        sistema = data['sistema']
        if not puede_administrar_sistema(request.user, sistema):
            return Response(
                {'error': f"No puede aprobar usuarios para '{sistema}'."},
                status=status.HTTP_403_FORBIDDEN,
            )

        rol = Rol.objects.filter(
            codigo=data['rol_codigo'], activo=True, deprecated=False,
        ).first()
        if rol is None:
            return Response(
                {'error': f"El rol '{data['rol_codigo']}' no existe o está "
                           'inactivo.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not puede_administrar_asignacion_rol(request.user, rol):
            return Response(
                {'error': 'No puede asignar el rol solicitado.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        sistemas_rol = SISTEMAS_POR_ROL.get(rol.codigo)
        if sistemas_rol is not None and sistema not in sistemas_rol:
            return Response(
                {'error': f"El rol '{rol.codigo}' no corresponde al sistema "
                          f"'{sistema}'."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        # El rol debe tener capacidades activas y coherentes con el sistema.
        if not rol.capacidades.filter(
            activo=True,
            sistema=sistema,
            codigo__startswith=f'{sistema}.',
        ).exists():
            return Response(
                {'error': f"El rol '{rol.codigo}' no tiene capacidades del "
                          f"sistema '{sistema}'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        unidad = UnidadOrganizacional.objects.get(
            pk=data['unidad_organizacional_id'],
        )
        fiscal_year_id = data.get('fiscal_year_id')
        fiscal_year = (
            GestionFiscal.objects.get(pk=fiscal_year_id)
            if fiscal_year_id is not None else None
        )
        validar_gestion_fiscal_asignacion(rol, unidad, fiscal_year)

        alcance_scope = SCOPES_FIJOS_ROLES_SISTEMA.get(
            rol.codigo, data['scope_type'],
        )

        AlcanceOrganizacional.objects.create(
            usuario=usuario,
            unidad=unidad,
            rol=rol,
            scope_type=alcance_scope,
            fiscal_year=fiscal_year,
        )
        usuario.roles.set([rol])
        usuario.estado = Usuario.ESTADO_ACTIVO
        usuario.is_active = True
        usuario.save(update_fields=['estado', 'is_active'])

        logger.info(
            'Solicitud aprobada: %s como %s (%s) por %s',
            usuario.email, rol.codigo, sistema, request.user.email,
        )
        return Response({
            'id': str(usuario.id),
            'email': usuario.email,
            'first_name': usuario.first_name,
            'last_name': usuario.last_name,
            'estado': usuario.estado,
            'activo': usuario.activo,
            'roles': [rol.codigo],
        })


class SolicitudesListView(generics.ListAPIView):
    """GET /api/v2/admin/solicitudes/ — usuarios PENDIENTE (paginado)."""

    serializer_class = SolicitudSerializer
    authentication_classes = [JWTAuthentication]
    pagination_class = PageNumberPagination

    def get_permissions(self):
        return [TieneCapacidad('accounts.solicitud.view')]

    def get_queryset(self):
        return (
            Usuario.objects.filter(estado=Usuario.ESTADO_PENDIENTE)
            .prefetch_related('alcances_organizacionales__unidad')
            .order_by('date_joined')
        )
