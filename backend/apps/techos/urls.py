from rest_framework.routers import DefaultRouter
from .views import TechoPresupuestarioViewSet, DistribucionTechoViewSet

router = DefaultRouter()
router.register(r'techos', TechoPresupuestarioViewSet)
router.register(r'distribuciones-techo', DistribucionTechoViewSet)

urlpatterns = router.urls
