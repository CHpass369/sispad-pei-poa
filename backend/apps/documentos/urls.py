from django.urls import path
from rest_framework.routers import DefaultRouter

from .descarga import descargar_documento
from .views import DocumentoAdjuntoViewSet

router = DefaultRouter()
router.register(r'documentos', DocumentoAdjuntoViewSet)

urlpatterns = router.urls

urlpatterns = urlpatterns + [
    path('documentos/<uuid:documento_id>/descargar/', descargar_documento,
         name='descargar-documento'),
]
