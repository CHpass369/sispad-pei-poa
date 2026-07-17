from rest_framework.routers import DefaultRouter
from .views import (
    EvaluacionViewSet, CriterioEvaluacionViewSet,
    ResultadoEvaluacionViewSet, LeccionAprendidaViewSet,
    RecomendacionViewSet,
)

router = DefaultRouter()
router.register(r'evaluaciones', EvaluacionViewSet)
router.register(r'criterios-evaluacion', CriterioEvaluacionViewSet)
router.register(r'resultados-evaluacion', ResultadoEvaluacionViewSet)
router.register(r'lecciones-aprendidas', LeccionAprendidaViewSet)
router.register(r'recomendaciones', RecomendacionViewSet)

urlpatterns = router.urls
