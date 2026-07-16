from rest_framework.routers import DefaultRouter
from .views import (
    ClasificadorInstitucionalViewSet, RubroRecursoViewSet,
    ObjetoGastoViewSet, FuenteFinanciamientoViewSet,
    OrganismoFinanciadorViewSet, EntidadTransferenciaViewSet,
    FinalidadFuncionViewSet, UnidadMedidaViewSet,
    TipoOperacionViewSet, TipoProductoViewSet,
    TipoProyectoViewSet, TipoFinanciamientoViewSet,
    VersionCatalogoViewSet
)

router = DefaultRouter()
router.register(r'clasificadores-institucionales', ClasificadorInstitucionalViewSet)
router.register(r'rubros', RubroRecursoViewSet)
router.register(r'objetos-gasto', ObjetoGastoViewSet)
router.register(r'fuentes', FuenteFinanciamientoViewSet)
router.register(r'organismos', OrganismoFinanciadorViewSet)
router.register(r'entidades-transferencia', EntidadTransferenciaViewSet)
router.register(r'finalidades-funciones', FinalidadFuncionViewSet)
router.register(r'unidades-medida', UnidadMedidaViewSet)
router.register(r'tipos-operacion', TipoOperacionViewSet)
router.register(r'tipos-producto', TipoProductoViewSet)
router.register(r'tipos-proyecto', TipoProyectoViewSet)
router.register(r'tipos-financiamiento', TipoFinanciamientoViewSet)
router.register(r'versiones-catalogo', VersionCatalogoViewSet)

urlpatterns = router.urls
