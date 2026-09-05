from rest_framework.routers import DefaultRouter
from .views import (
    CodigoNivelViewSet, AcuerdoInternacionalViewSet, NormativaViewSet,
    LineamientoPADViewSet, ResultadoPADViewSet, ProductoPADViewSet,
    ResultadoPEIViewSet, ProductoPEIViewSet, ArticulacionPADPEIViewSet,
    IndicadorCadenaViewSet, AccionPOAViewSet, OperacionPOAUViewSet,
    ActividadPOAUViewSet, ActividadNormativaViewSet, TareaPOAUViewSet,
    TareaNormativaViewSet, SeguimientoPresupuestoViewSet,
    AsignacionObjetoGastoViewSet, BorradorMatrizPADViewSet,
    BorradorMatrizPEIViewSet, BorradorMatrizPOAViewSet,
)
from .views_matrices import MatrizViewSet
from .views_poau import MatrizPOAUViewSet
from .views_saldos import SaldoUnidadCategoriaViewSet

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
router.register(r'borradores-matriz-pad', BorradorMatrizPADViewSet)
router.register(r'borradores-matriz-pei', BorradorMatrizPEIViewSet)
router.register(r'borradores-matriz-poa', BorradorMatrizPOAViewSet)
router.register(r'matrices', MatrizViewSet, basename='matrices')
router.register(r'matriz-poau', MatrizPOAUViewSet, basename='matriz-poau')
router.register(r'saldos-unidad-categoria', SaldoUnidadCategoriaViewSet,
                basename='saldos-unidad-categoria')

urlpatterns = router.urls
