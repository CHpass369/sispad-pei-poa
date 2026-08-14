"""Urlconf para settings_test_sqlite: rutas v1 (apps no-geo) + v2 sin SIS-PRO.

La API V2 completa incluye el router de SIS-PRO (apps.inversion), que usa
modelos PostGIS; en SQLite se registran solo los namespaces de las apps
no-geo (platform, sis-pe, sis-poa, me).
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.core.views_root import health_check

from apps.accounts.views_v2 import MeViewSet
from apps.evaluacion.views_v2 import (
    EvaluacionV2ViewSet,
    LeccionV2ViewSet,
    RecomendacionV2ViewSet,
)
from apps.planificacion.views_v2 import (
    InstrumentoViewSet,
    MetodologiaViewSet,
    NodoViewSet,
    TipoInstrumentoViewSet,
    VersionViewSet,
    VinculoViewSet,
)
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
sis_pe_router = DefaultRouter()
sis_poa_router = DefaultRouter()

sis_pe_router.register('instrumentos', InstrumentoViewSet, basename='v2-instrumentos')
sis_pe_router.register('versiones', VersionViewSet, basename='v2-versiones')
sis_pe_router.register('nodos', NodoViewSet, basename='v2-nodos')
sis_pe_router.register('vinculos', VinculoViewSet, basename='v2-vinculos')
sis_pe_router.register('tipos-instrumento', TipoInstrumentoViewSet, basename='v2-tipos-instrumento')
sis_pe_router.register('metodologias', MetodologiaViewSet, basename='v2-metodologias')
sis_pe_router.register('evaluaciones', EvaluacionV2ViewSet, basename='v2-evaluaciones')
sis_pe_router.register('lecciones', LeccionV2ViewSet, basename='v2-lecciones')
sis_pe_router.register('recomendaciones', RecomendacionV2ViewSet, basename='v2-recomendaciones')

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
    path('api/v1/', include('apps.evaluacion.urls')),
    path('api/v1/', include('apps.modificaciones.urls')),
    path('api/v1/', include('apps.notificaciones.urls')),
    path('api/v1/', include('apps.seguimiento.urls')),
    path('api/v1/articulacion/', include('apps.articulacion.urls')),
    path('api/v2/platform/', include(platform_router.urls)),
    path('api/v2/sis-pe/', include(sis_pe_router.urls)),
    path('api/v2/sis-poa/', include(sis_poa_router.urls)),
    path('api/v2/', include(me_router.urls)),
]
