"""Contratos del kernel estratégico V2 (WP-04 / SIS-PE)."""
from datetime import date

import pytest

pytestmark = pytest.mark.skip(
    reason='La API /api/v2/sis-pe/ se retiro junto con el nucleo estrategico (planificacion.Instrumento, VersionInstrumento y TipoInstrumento ya no existen; las rutas devuelven 404). Los tests se conservan como especificacion para cuando se reconstruya SIS-PE.'
)
from django.core.exceptions import ValidationError
from rest_framework.test import APIClient

from apps.accounts.models import Rol, Usuario


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def usuario_editor(db):
    user = Usuario.objects.create_user(
        email='editor@test.gob.bo', password='test123',
    )
    rol = Rol.objects.get(codigo='admin_poa')
    user.roles.add(rol)
    return user


@pytest.fixture
def usuario_lector(db):
    user = Usuario.objects.create_user(
        email='lector@test.gob.bo', password='test123',
    )
    rol = Rol.objects.get(codigo='consulta')
    user.roles.add(rol)
    return user


def _client(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


# ---------------------------------------------------------------------------
# Modelos
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# API V2
# ---------------------------------------------------------------------------
def test_instrumento_requiere_autenticacion():
    assert APIClient().get('/api/v2/sis-pe/instrumentos/').status_code == 401


def test_listar_instrumentos_como_lector(usuario_lector):
    response = _client(usuario_lector).get('/api/v2/sis-pe/instrumentos/')
    assert response.status_code == 200
    data = response.json()
    assert data['count'] == 1
    items = data['results']
    assert items[0]['codigo'] == 'PAD-2027'
    assert items[0]['tipo_nombre'] == 'Plan Anual de Desarrollo'


@pytest.fixture
def usuario_v2_super(db):
    user = Usuario.objects.create_superuser(
        email='kernel-super@test.gob.bo', password='test123',
    )
    return user


def test_schema_v2_incluye_sis_pe(usuario_v2_super):
    import json
    client = _client(usuario_v2_super)
    response = client.get('/api/v2/schema/', HTTP_ACCEPT='application/json')
    data = json.loads(response.content)
    assert '/api/v2/sis-pe/instrumentos/' in data['paths']
    assert '/api/v2/sis-pe/versiones/' in data['paths']
    assert '/api/v2/sis-pe/vinculos/' in data['paths']
