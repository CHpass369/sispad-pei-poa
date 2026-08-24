"""Urlconf para settings_test_sqlite: rutas v1 (apps no-geo) + v2.

Se registran solo los namespaces de las apps no-geo (platform, sis-poa, me),
porque el resto usa modelos PostGIS que SQLite no soporta.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.core.views_root import health_check

from apps.accounts.views_v2 import MeViewSet
from apps.poau.views_v2 import (
    AccionViewSet,
    ActividadViewSet,
    OperacionViewSet,
    PoAViewSet,
    ProgramacionViewSet,
    TareaViewSet,
)
from apps.techos.views_v2 import TechoViewSetV2
from apps.workflow.views_v2 import (
    DefinicionViewSet,
    InstanciaViewSet,
    TareaViewSet as WorkflowTareaViewSet,
)

platform_router = DefaultRouter()
sis_poa_router = DefaultRouter()


sis_poa_router.register('poas', PoAViewSet, basename='v2-poas')
sis_poa_router.register('acciones', AccionViewSet, basename='v2-acciones-poa')
sis_poa_router.register('operaciones', OperacionViewSet, basename='v2-operaciones')
sis_poa_router.register('actividades', ActividadViewSet, basename='v2-actividades')
sis_poa_router.register('tareas', TareaViewSet, basename='v2-tareas')
sis_poa_router.register('programaciones', ProgramacionViewSet, basename='v2-programaciones')
sis_poa_router.register('techos', TechoViewSetV2, basename='v2-techos')

platform_router.register('workflow-definiciones', DefinicionViewSet, basename='v2-workflow-definiciones')
platform_router.register('workflow-instancias', InstanciaViewSet, basename='v2-workflow-instancias')
platform_router.register('workflow-tareas', WorkflowTareaViewSet, basename='v2-workflow-tareas')

me_router = DefaultRouter()
me_router.register('me', MeViewSet, basename='v2-me')

urlpatterns = [
    path('health/', health_check, name='health'),
    path('api/v1/auth/', include('apps.accounts.urls')),
    path('api/v1/', include('apps.core.urls')),
    path('api/v1/', include('apps.gestion.urls')),
    path('api/v1/', include('apps.organizacion.urls')),
    path('api/v1/', include('apps.catalogos.urls')),
    path('api/v1/', include('apps.normativa.urls')),
    path('api/v1/', include('apps.planificacion.urls')),
    path('api/v1/planificacion/', include('apps.planificacion.urls')),
    path('api/v1/', include('apps.indicadores.urls')),
    path('api/v1/', include('apps.recursos.urls')),
    path('api/v1/', include('apps.techos.urls')),
    path('api/v1/', include('apps.presupuesto.urls')),
    path('api/v1/pad/', include('apps.pad.urls')),
    path('api/v1/', include('apps.workflow.urls')),
    path('api/v1/', include('apps.documentos.urls')),
    path('api/v1/', include('apps.auditoria.urls')),
    path('api/v1/poau/', include('apps.poau.urls')),
    path('api/v1/', include('apps.modificaciones.urls')),
    path('api/v1/', include('apps.notificaciones.urls')),
    path('api/v1/', include('apps.seguimiento.urls')),
    path('api/v1/articulacion/', include('apps.articulacion.urls')),
    path('api/v2/platform/', include(platform_router.urls)),
    path('api/v2/sis-poa/', include(sis_poa_router.urls)),
    path('api/v2/', include(me_router.urls)),
]
