from rest_framework.routers import DefaultRouter
from .views import (
    PlanViewSet, NodoPlanificacionViewSet,
    AccionMedianoPlazoViewSet, AccionCortoPlazoViewSet,
    ArticulacionPlanificacionViewSet, FormulacionViewSet
)
from .articulacion_api import ArticulacionViewSet

router = DefaultRouter()
router.register(r'planes', PlanViewSet)
router.register(r'nodos-planificacion', NodoPlanificacionViewSet)
router.register(r'acciones-mediano-plazo', AccionMedianoPlazoViewSet)
router.register(r'acciones-corto-plazo', AccionCortoPlazoViewSet)
router.register(r'articulaciones', ArticulacionPlanificacionViewSet)
router.register(r'formulacion', FormulacionViewSet, basename='formulacion')
router.register(r'articular', ArticulacionViewSet, basename='articular')

urlpatterns = router.urls
