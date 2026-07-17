from rest_framework.routers import DefaultRouter
from .views import (
    SolicitudModificacionViewSet,
    CambioModificacionViewSet,
    ImpactoModificacionViewSet,
)

router = DefaultRouter()
router.register(r'solicitudes-modificacion', SolicitudModificacionViewSet)
router.register(r'cambios-modificacion', CambioModificacionViewSet)
router.register(r'impactos-modificacion', ImpactoModificacionViewSet)

urlpatterns = router.urls
