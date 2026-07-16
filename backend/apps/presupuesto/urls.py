from rest_framework.routers import DefaultRouter
from .views import (
    ProgramaPresupuestarioViewSet, ProyectoPresupuestarioViewSet,
    ActividadPresupuestariaViewSet, LineaPresupuestariaViewSet
)

router = DefaultRouter()
router.register(r'programas', ProgramaPresupuestarioViewSet)
router.register(r'proyectos-presupuestarios', ProyectoPresupuestarioViewSet)
router.register(r'actividades-presupuestarias', ActividadPresupuestariaViewSet)
router.register(r'lineas-presupuestarias', LineaPresupuestariaViewSet)

urlpatterns = router.urls
