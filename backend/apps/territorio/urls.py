from rest_framework.routers import DefaultRouter
from .views import DistritoViewSet, UnidadTerritorialViewSet, LocalizacionTerritorialViewSet

router = DefaultRouter()
router.register(r'distritos', DistritoViewSet)
router.register(r'unidades-territoriales', UnidadTerritorialViewSet)
router.register(r'localizaciones', LocalizacionTerritorialViewSet)

urlpatterns = router.urls
