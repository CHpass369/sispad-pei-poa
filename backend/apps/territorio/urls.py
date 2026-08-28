from rest_framework.routers import DefaultRouter
from .views import (
    DirigenteTerritorialViewSet, DistritoViewSet, LocalizacionTerritorialViewSet,
    UnidadTerritorialViewSet,
)

router = DefaultRouter()
router.register(r'distritos', DistritoViewSet)
router.register(r'unidades-territoriales', UnidadTerritorialViewSet)
router.register(r'dirigentes-territoriales', DirigenteTerritorialViewSet)
router.register(r'localizaciones', LocalizacionTerritorialViewSet)

urlpatterns = router.urls
