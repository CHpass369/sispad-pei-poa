from rest_framework.routers import DefaultRouter
from .views import (
    TipoUnidadViewSet, UnidadOrganizacionalViewSet,
    DireccionAdministrativaViewSet, UnidadEjecutoraViewSet,
    AsignacionUsuarioUnidadViewSet
)

router = DefaultRouter()
router.register(r'tipos-unidad', TipoUnidadViewSet)
router.register(r'unidades', UnidadOrganizacionalViewSet)
router.register(r'direcciones-administrativas', DireccionAdministrativaViewSet)
router.register(r'unidades-ejecutoras', UnidadEjecutoraViewSet)
router.register(r'asignaciones-usuario-unidad', AsignacionUsuarioUnidadViewSet)

urlpatterns = router.urls
