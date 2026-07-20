from rest_framework.routers import DefaultRouter
from .views import (
    ReporteSeguimientoViewSet,
    EntradaSeguimientoViewSet,
    AlertaViewSet,
    UmbralConfiguracionViewSet,
)

router = DefaultRouter()
router.register(r'reportes', ReporteSeguimientoViewSet)
router.register(r'entradas', EntradaSeguimientoViewSet, basename='entrada-seguimiento')
router.register(r'alertas', AlertaViewSet)
router.register(r'umbrales', UmbralConfiguracionViewSet)

urlpatterns = router.urls
