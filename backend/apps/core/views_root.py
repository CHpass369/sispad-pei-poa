from django.http import JsonResponse
from django.shortcuts import redirect


def root_redirect(request):
    """Redirige la raíz a la documentación de la API."""
    return redirect('/api/v1/docs/')


def health_check(request):
    """Health check para monitoreo."""
    return JsonResponse({
        'status': 'ok',
        'sistema': 'SISPOA Sacaba',
        'version': '1.0.0',
    })
