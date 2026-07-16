from rest_framework.routers import DefaultRouter
from .views import (
    IndicadorViewSet, MetaProgramadaViewSet,
    OperacionViewSet, TareaViewSet,
    ProductoViewSet, MedioVerificacionViewSet,
    SupuestoViewSet
)

router = DefaultRouter()
router.register(r'indicadores', IndicadorViewSet)
router.register(r'metas-programadas', MetaProgramadaViewSet)
router.register(r'operaciones', OperacionViewSet)
router.register(r'tareas', TareaViewSet)
router.register(r'productos', ProductoViewSet)
router.register(r'medios-verificacion', MedioVerificacionViewSet)
router.register(r'supuestos', SupuestoViewSet)

urlpatterns = router.urls
