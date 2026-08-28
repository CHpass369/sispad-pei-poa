"""
FASE 10 — Headers de deprecación de la API V1 (RFC 8594).

La estrategia está documentada en docs/refactor-pip/LEGACY_DEPRECATION.md.
Los tests usan el cliente Django (no APIClient de DRF) porque el
mecanismo es un middleware puro, no una capa de DRF.
"""
from django.test import Client


def test_v1_response_carries_deprecation_headers():
    # /api/v1/dashboard/poa/ existe y sin auth responde 401/403 (IsAuthenticated),
    # nunca 404: el middleware debe marcar igualmente la respuesta.
    response = Client().get('/api/v1/dashboard/poa/')
    assert response.status_code in (401, 403)
    assert response['Deprecation'] == 'true'
    assert response['Sunset'] == 'Sun, 01 Jan 2027 00:00:00 GMT'
    assert 'rel="deprecation"' in response['Link']
    assert 'LEGACY_DEPRECATION.md' in response['Link']


def test_v2_response_has_no_deprecation_headers():
    response = Client().get('/api/v2/me/')
    assert response.status_code in (401, 403)
    assert 'Deprecation' not in response
    assert 'Sunset' not in response
    assert 'Link' not in response


def test_health_has_no_deprecation_headers():
    response = Client().get('/health/')
    assert 'Deprecation' not in response
    assert 'Sunset' not in response
