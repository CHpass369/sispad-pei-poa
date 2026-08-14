from rest_framework.routers import DefaultRouter
from .views import (
    PlanViewSet, NodoPlanificacionViewSet,
    AccionMedianoPlazoViewSet, AccionCortoPlazoViewSet,
    ArticulacionPlanificacionViewSet,
    PlanVersionViewSet, MatrizCompletaViewSet,
)
from .articulacion_api import ArticulacionViewSet

router = DefaultRouter()
router.register(r'planes', PlanViewSet)
router.register(r'versiones-plan', PlanVersionViewSet)
router.register(r'nodos-planificacion', NodoPlanificacionViewSet)
router.register(r'acciones-mediano-plazo', AccionMedianoPlazoViewSet)
router.register(r'acciones-corto-plazo', AccionCortoPlazoViewSet)
router.register(r'articulaciones', ArticulacionPlanificacionViewSet)
router.register(r'articular', ArticulacionViewSet, basename='articular')
router.register(r'matriz-completa', MatrizCompletaViewSet, basename='matriz-completa')

urlpatterns = router.urls
