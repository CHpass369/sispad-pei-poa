from rest_framework.routers import DefaultRouter
from .views import (
    ProyectoInversionViewSet, ProgramacionPlurianualProyectoViewSet,
    ProgramacionFisicaFinancieraViewSet
)

router = DefaultRouter()
router.register(r'proyectos-inversion', ProyectoInversionViewSet)
router.register(r'programacion-plurianual', ProgramacionPlurianualProyectoViewSet)
router.register(r'programacion-fisica-financiera', ProgramacionFisicaFinancieraViewSet)

urlpatterns = router.urls
