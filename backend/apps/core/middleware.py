"""Middlewares de la API PIP-GAMS."""

from django.conf import settings


class DeprecationV1Middleware:
    """Marca las respuestas de la API V1 con headers de deprecación (RFC 8594).

    Toda respuesta cuyo path comience con ``/api/v1/`` lleva:

        Deprecation: true
        Sunset: <fecha de retiro sugerida>
        Link: <docs>; rel="deprecation"

    La fecha y el enlace son configurables vía ``API_V1_SUNSET`` y
    ``API_V1_DEPRECATION_LINK``. /api/v2/, /health/ y el resto del sitio
    NO reciben estos headers.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.sunset = getattr(settings, 'API_V1_SUNSET', 'Sun, 01 Jan 2027 00:00:00 GMT')
        self.link = getattr(
            settings, 'API_V1_DEPRECATION_LINK',
            '/docs/refactor-pip/LEGACY_DEPRECATION.md',
        )

    def __call__(self, request):
        response = self.get_response(request)
        if request.path.startswith('/api/v1/'):
            response['Deprecation'] = 'true'
            response['Sunset'] = self.sunset
            response['Link'] = f'<{self.link}>; rel="deprecation"'
        return response
