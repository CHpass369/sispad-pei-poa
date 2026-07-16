from rest_framework.routers import DefaultRouter
from .views import (
    EnvioFormulacionViewSet, RevisionViewSet,
    ObservacionViewSet, AprobacionViewSet,
    ConsolidacionViewSet,
)

router = DefaultRouter()
router.register(r'envios', EnvioFormulacionViewSet)
router.register(r'revisiones', RevisionViewSet)
router.register(r'observaciones', ObservacionViewSet)
router.register(r'aprobaciones', AprobacionViewSet)
router.register(r'consolidacion', ConsolidacionViewSet, basename='consolidacion')

urlpatterns = router.urls
