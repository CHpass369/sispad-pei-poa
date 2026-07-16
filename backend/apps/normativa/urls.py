from rest_framework.routers import DefaultRouter
from .views import VersionNormativaViewSet, ReglaPresupuestariaLegalViewSet

router = DefaultRouter()
router.register(r'versiones-normativa', VersionNormativaViewSet)
router.register(r'reglas-presupuestarias', ReglaPresupuestariaLegalViewSet)

urlpatterns = router.urls
