from rest_framework.routers import DefaultRouter
from .views import TechoPresupuestarioViewSet, DistribucionTechoViewSet, MovimientoTechoViewSet

router = DefaultRouter()
router.register(r'techos', TechoPresupuestarioViewSet)
router.register(r'distribuciones-techo', DistribucionTechoViewSet)
router.register(r'movimientos-techo', MovimientoTechoViewSet)

urlpatterns = router.urls
