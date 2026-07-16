from rest_framework.routers import DefaultRouter
from .views import GestionFiscalViewSet, CicloFormulacionViewSet, EtapaFormulacionViewSet

router = DefaultRouter()
router.register(r'gestiones', GestionFiscalViewSet)
router.register(r'ciclos', CicloFormulacionViewSet)
router.register(r'etapas', EtapaFormulacionViewSet)

urlpatterns = router.urls
