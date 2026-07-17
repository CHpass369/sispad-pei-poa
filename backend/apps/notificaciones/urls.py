from rest_framework.routers import DefaultRouter
from .views import (
    TipoNotificacionViewSet,
    NotificacionViewSet,
    PreferenciaNotificacionViewSet,
)

router = DefaultRouter()
router.register(r'tipos', TipoNotificacionViewSet)
router.register(r'notificaciones', NotificacionViewSet, basename='notificacion')
router.register(r'preferencias', PreferenciaNotificacionViewSet)

urlpatterns = router.urls
