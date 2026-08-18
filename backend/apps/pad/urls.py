from rest_framework.routers import DefaultRouter

from .views import SectorPADViewSet

router = DefaultRouter()
router.register(r'sectores-pad', SectorPADViewSet)

urlpatterns = router.urls
