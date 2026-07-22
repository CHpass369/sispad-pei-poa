from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from pathlib import Path
from django.http import FileResponse, Http404
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
    path(f'{api_prefix}articulacion/', include('apps.articulacion.urls')),
    path(f'{api_prefix}', include('apps.acciones_correctivas.urls')),
    path(f'{api_prefix}schema/', SpectacularAPIView.as_view(), name='schema'),
    path(f'{api_prefix}docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='docs'),
]

# Servir frontend Angular compilado (SPA)
import mimetypes

FRONTEND_DIR = Path(settings.BASE_DIR / 'static_assets')

def serve_frontend(request, path=''):
    """Sirve estáticos o index.html para SPA. No intercepta api/ admin/ ni health/."""
    # No tocar rutas de API, admin o health
    if path.startswith('api/') or path.startswith('admin/') or path.startswith('health/'):
        from django.http import HttpResponse
        return HttpResponse(status=404)

    filepath = FRONTEND_DIR / path
    if filepath.exists() and filepath.is_file():
        content_type, _ = mimetypes.guess_type(str(filepath))
        return FileResponse(open(filepath, 'rb'), content_type=content_type or 'application/octet-stream')

    # SPA catch-all: servir index.html
    idx = FRONTEND_DIR / 'index.html'
    if idx.exists():
        return FileResponse(open(idx, 'rb'), content_type='text/html')
    raise Http404('Frontend no compilado')

# Catch-all para todo lo que no sea api/admin/health
urlpatterns += [
    re_path(r'^(?P<path>.*)$', serve_frontend, name='spa'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
