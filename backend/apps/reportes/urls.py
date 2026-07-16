from rest_framework.routers import DefaultRouter
from .views import ReporteGeneradoViewSet

router = DefaultRouter()
router.register(r'reportes', ReporteGeneradoViewSet)

urlpatterns = router.urls
