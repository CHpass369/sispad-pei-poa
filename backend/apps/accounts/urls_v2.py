"""Rutas V2 de accounts: registro y administración de usuarios.

Se incluyen sin prefijo adicional desde config.urls_v2, de modo que quedan:

- /api/v2/auth/register/
- /api/v2/auth/organizational-units/
- /api/v2/admin/users/<uuid>/approve/
- /api/v2/admin/users/
- /api/v2/admin/users/<uuid>/
- /api/v2/admin/users/<uuid>/activate/
- /api/v2/admin/users/<uuid>/deactivate/
- /api/v2/admin/users/<uuid>/assignments/
- /api/v2/admin/solicitudes/
- /api/v2/admin/roles/
- /api/v2/admin/roles/<uuid>/
- /api/v2/admin/roles/<uuid>/capabilities/
- /api/v2/admin/capabilities/
"""
from django.urls import path

from apps.accounts.views_admin import (
    ActivarUsuarioView,
    AsignacionesUsuarioView,
    AsignarCapacidadesRolView,
    CapacidadAdminListView,
    DesactivarUsuarioView,
    PreviewAccessView,
    RolAdminDetailView,
    RolAdminListCreateView,
    UsuarioAdminDetailView,
    UsuarioAdminListView,
)
from apps.accounts.views_register import (
    AprobarUsuarioView,
    RegistroPublicoView,
    SolicitudesListView,
    UnidadesOrganizacionalesPublicasView,
)

urlpatterns = [
    path(
        'auth/register/', RegistroPublicoView.as_view(),
        name='v2-auth-register',
    ),
    path(
        'auth/organizational-units/',
        UnidadesOrganizacionalesPublicasView.as_view(),
        name='v2-auth-organizational-units',
    ),
    path(
        'admin/preview-access/', PreviewAccessView.as_view(),
        name='v2-admin-preview-access',
    ),
    path(
        'admin/users/<uuid:pk>/approve/', AprobarUsuarioView.as_view(),
        name='v2-admin-user-approve',
    ),
    path(
        'admin/users/', UsuarioAdminListView.as_view(),
        name='v2-admin-users',
    ),
    path(
        'admin/users/<uuid:pk>/', UsuarioAdminDetailView.as_view(),
        name='v2-admin-user-detail',
    ),
    path(
        'admin/users/<uuid:pk>/activate/', ActivarUsuarioView.as_view(),
        name='v2-admin-user-activate',
    ),
    path(
        'admin/users/<uuid:pk>/deactivate/', DesactivarUsuarioView.as_view(),
        name='v2-admin-user-deactivate',
    ),
    path(
        'admin/users/<uuid:pk>/assignments/',
        AsignacionesUsuarioView.as_view(),
        name='v2-admin-user-assignments',
    ),
    path(
        'admin/solicitudes/', SolicitudesListView.as_view(),
        name='v2-admin-solicitudes',
    ),
    path(
        'admin/roles/', RolAdminListCreateView.as_view(),
        name='v2-admin-roles',
    ),
    path(
        'admin/roles/<uuid:pk>/', RolAdminDetailView.as_view(),
        name='v2-admin-role-detail',
    ),
    path(
        'admin/roles/<uuid:pk>/capabilities/',
        AsignarCapacidadesRolView.as_view(),
        name='v2-admin-role-capabilities',
    ),
    path(
        'admin/capabilities/', CapacidadAdminListView.as_view(),
        name='v2-admin-capabilities',
    ),
]
