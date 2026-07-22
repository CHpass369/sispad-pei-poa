from rest_framework.routers import DefaultRouter
from .views import (
    CodigoNivelViewSet, AcuerdoInternacionalViewSet, NormativaViewSet,
    LineamientoPADViewSet, ResultadoPADViewSet, ProductoPADViewSet,
    ResultadoPEIViewSet, ProductoPEIViewSet, ArticulacionPADPEIViewSet,
    IndicadorCadenaViewSet, AccionPOAViewSet, OperacionPOAUViewSet,
    ActividadPOAUViewSet, ActividadNormativaViewSet, TareaPOAUViewSet,
    TareaNormativaViewSet, SeguimientoPresupuestoViewSet,
    AsignacionObjetoGastoViewSet,
)

router = DefaultRouter()
router.register(r'resultados-pad', ResultadoPADViewSet)
router.register(r'productos-pad', ProductoPADViewSet)
router.register(r'resultados-pei', ResultadoPEIViewSet)
router.register(r'productos-pei', ProductoPEIViewSet)
router.register(r'articulaciones-pad-pei', ArticulacionPADPEIViewSet)
router.register(r'indicadores', IndicadorCadenaViewSet)
router.register(r'acciones-poa', AccionPOAViewSet)
router.register(r'operaciones', OperacionPOAUViewSet)
router.register(r'actividades', ActividadPOAUViewSet)
router.register(r'normativas-actividad', ActividadNormativaViewSet)
router.register(r'tareas', TareaPOAUViewSet)
router.register(r'normativas-tarea', TareaNormativaViewSet)
router.register(r'seguimientos', SeguimientoPresupuestoViewSet)
router.register(r'asignaciones-gasto', AsignacionObjetoGastoViewSet)
router.register(r'acuerdos', AcuerdoInternacionalViewSet)
router.register(r'normativas', NormativaViewSet)
router.register(r'codigos-nivel', CodigoNivelViewSet)
router.register(r'lineamientos-pad', LineamientoPADViewSet)

urlpatterns = router.urls
