"""Rutas V2 de accounts (F3a): registro público y administración de solicitudes.

Se incluyen sin prefijo adicional desde config.urls_v2, de modo que quedan:

- /api/v2/auth/register/
- /api/v2/admin/users/<uuid>/approve/
- /api/v2/admin/solicitudes/
"""
from django.urls import path

from apps.accounts.views_register import (
    AprobarUsuarioView,
    RegistroPublicoView,
    SolicitudesListView,
)

urlpatterns = [
    path(
        'auth/register/', RegistroPublicoView.as_view(),
        name='v2-auth-register',
    ),
    path(
        'admin/users/<uuid:pk>/approve/', AprobarUsuarioView.as_view(),
        name='v2-admin-user-approve',
    ),
    path(
        'admin/solicitudes/', SolicitudesListView.as_view(),
        name='v2-admin-solicitudes',
    ),
]
