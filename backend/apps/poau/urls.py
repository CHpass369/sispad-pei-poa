from rest_framework.routers import DefaultRouter
from .views import (
    POAUViewSet, POAUActividadViewSet,
    EjecucionFisicaViewSet, EjecucionFinancieraViewSet,
)

router = DefaultRouter()
router.register(r'poaus', POAUViewSet)
router.register(r'actividades', POAUActividadViewSet)
router.register(r'ejecucion-fisica', EjecucionFisicaViewSet)
router.register(r'ejecucion-financiera', EjecucionFinancieraViewSet)

urlpatterns = router.urls
