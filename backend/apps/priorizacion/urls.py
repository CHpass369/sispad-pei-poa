from rest_framework.routers import DefaultRouter

from .views import (
    ActaPriorizacionViewSet, CategoriaProgramaticaViewSet,
    MatrizPriorizacionViewSet, ProyectoCatalogoViewSet,
    SaldoFinanciamientoViewSet,
)

router = DefaultRouter()
router.register(r'catalogo-proyectos', ProyectoCatalogoViewSet,
                basename='catalogo-proyectos')
router.register(r'actas', ActaPriorizacionViewSet, basename='actas')
router.register(r'matrices', MatrizPriorizacionViewSet, basename='matrices-priorizacion')
router.register(r'categorias-programaticas', CategoriaProgramaticaViewSet,
                basename='categorias-programaticas')
router.register(r'saldos', SaldoFinanciamientoViewSet, basename='saldos')

urlpatterns = router.urls
