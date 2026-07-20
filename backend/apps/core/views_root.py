from django.http import FileResponse, JsonResponse
from django.conf import settings


def root_redirect(request):
    """Sirve el frontend Angular compilado en la raíz."""
    frontend_index = settings.BASE_DIR / 'static_assets' / 'index.html'
    if frontend_index.exists():
        return FileResponse(open(frontend_index, 'rb'))
    return JsonResponse({'sistema': 'SISPOA Sacaba', 'frontend': 'no compilado'})


def health_check(request):
    """Health check para monitoreo."""
    return JsonResponse({
        'status': 'ok',
        'sistema': 'SISPOA Sacaba',
        'version': '1.0.0',
    })
