from rest_framework.routers import DefaultRouter
from .views import AccionCorrectivaViewSet, CompromisoAccionCorrectivaViewSet

router = DefaultRouter()
router.register(r'acciones-correctivas', AccionCorrectivaViewSet)
router.register(r'compromisos-accion-correctiva', CompromisoAccionCorrectivaViewSet)

urlpatterns = router.urls
