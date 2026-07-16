from rest_framework.routers import DefaultRouter
from .views import (
    SectorPADViewSet, PoliticaPADViewSet, LineamientoEstrategicoViewSet,
    ResultadoTerritorialViewSet, ProductoTerritorialViewSet,
    ArticulacionSIPEBViewSet, ProgramacionAnualPADViewSet,
)

router = DefaultRouter()
router.register(r'sectores-pad', SectorPADViewSet)
router.register(r'politicas-pad', PoliticaPADViewSet)
router.register(r'lineamientos', LineamientoEstrategicoViewSet)
router.register(r'resultados-territoriales', ResultadoTerritorialViewSet)
router.register(r'productos-territoriales', ProductoTerritorialViewSet)
router.register(r'articulaciones-sipeb', ArticulacionSIPEBViewSet)
router.register(r'programaciones-anuales', ProgramacionAnualPADViewSet, basename='programaciones-anuales')

urlpatterns = router.urls
