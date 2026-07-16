from rest_framework.routers import DefaultRouter
from .views import DocumentoAdjuntoViewSet

router = DefaultRouter()
router.register(r'documentos', DocumentoAdjuntoViewSet)

urlpatterns = router.urls
