from django.http import FileResponse, JsonResponse
from django.conf import settings


def root_redirect(request):
    """Sirve el frontend Angular compilado en la raíz."""
    frontend_index = settings.BASE_DIR / 'static_assets' / 'index.html'
    if frontend_index.exists():
        return FileResponse(open(frontend_index, 'rb'))
    return JsonResponse({'sistema': 'SISPOA Sacaba', 'frontend': 'no compilado'})


def health_check(request):
    """Health check para monitoreo (WP-12): incluye estado de la base."""
    db_ok = True
    try:
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
            cursor.fetchone()
    except Exception:
        db_ok = False

    payload = {
        'status': 'ok' if db_ok else 'degraded',
        'sistema': 'PIP-GAMS',
        'version': '1.0.0',
        'base_datos': 'ok' if db_ok else 'error',
    }
    from django.http import HttpResponse
    return JsonResponse(payload, status=200 if db_ok else 503)
