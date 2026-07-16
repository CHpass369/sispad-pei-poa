from rest_framework.routers import DefaultRouter
from .views import EventoAuditoriaViewSet

router = DefaultRouter()
router.register(r'eventos', EventoAuditoriaViewSet)

urlpatterns = router.urls
