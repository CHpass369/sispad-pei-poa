from rest_framework.routers import DefaultRouter
from .views import EstimacionRecursoViewSet, EstimacionPlurianualViewSet

router = DefaultRouter()
router.register(r'estimaciones', EstimacionRecursoViewSet)
router.register(r'estimaciones-plurianuales', EstimacionPlurianualViewSet)

urlpatterns = router.urls
