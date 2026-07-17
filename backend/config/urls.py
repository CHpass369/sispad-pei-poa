from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from apps.core.views_root import root_redirect, health_check

api_prefix = 'api/v1/'

urlpatterns = [
    path('', root_redirect, name='root'),
    path('health/', health_check, name='health'),
    path('admin/', admin.site.urls),
    path(f'{api_prefix}auth/', include('apps.accounts.urls')),
    path(f'{api_prefix}', include('apps.core.urls')),
    path(f'{api_prefix}', include('apps.gestion.urls')),
    path(f'{api_prefix}', include('apps.organizacion.urls')),
    path(f'{api_prefix}', include('apps.catalogos.urls')),
    path(f'{api_prefix}', include('apps.normativa.urls')),
    path(f'{api_prefix}', include('apps.planificacion.urls')),
    path(f'{api_prefix}', include('apps.indicadores.urls')),
    path(f'{api_prefix}', include('apps.recursos.urls')),
    path(f'{api_prefix}', include('apps.techos.urls')),
    path(f'{api_prefix}', include('apps.presupuesto.urls')),
    path(f'{api_prefix}', include('apps.inversion.urls')),
    path(f'{api_prefix}', include('apps.territorio.urls')),
    path(f'{api_prefix}pad/', include('apps.pad.urls')),
    path(f'{api_prefix}', include('apps.workflow.urls')),
    path(f'{api_prefix}', include('apps.documentos.urls')),
    path(f'{api_prefix}', include('apps.reportes.urls')),
    path(f'{api_prefix}', include('apps.auditoria.urls')),
    path(f'{api_prefix}poau/', include('apps.poau.urls')),
    path(f'{api_prefix}', include('apps.evaluacion.urls')),
    path(f'{api_prefix}', include('apps.modificaciones.urls')),
    path(f'{api_prefix}', include('apps.notificaciones.urls')),
    path(f'{api_prefix}', include('apps.seguimiento.urls')),
    path(f'{api_prefix}', include('apps.acciones_correctivas.urls')),
    path(f'{api_prefix}schema/', SpectacularAPIView.as_view(), name='schema'),
    path(f'{api_prefix}docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='docs'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
