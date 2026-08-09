"""Contratos de la API V2 de PIP-GAMS (WP-02)."""
import pytest
from rest_framework.test import APIClient

from apps.accounts.models import Rol, Usuario


@pytest.fixture
def usuario_v2(db):
    rol = Rol.objects.create(
        codigo='superadmin', nombre='Superadministrador', es_sistema=True,
    )
    user = Usuario.objects.create_user(
        email='v2@test.gob.bo', password='test123',
        first_name='V2', last_name='Test',
    )
    user.roles.add(rol)
    return user


@pytest.fixture
def auth_client_v2(usuario_v2):
    client = APIClient()
    client.force_authenticate(user=usuario_v2)
    return client


def test_me_requiere_autenticacion():
    client = APIClient()
    response = client.get('/api/v2/me/')
    assert response.status_code == 401


def test_me_devuelve_identidad_del_usuario(auth_client_v2, usuario_v2):
    response = auth_client_v2.get('/api/v2/me/')
    assert response.status_code == 200
    data = response.json()
    assert data['id'] == str(usuario_v2.id)
    assert data['email'] == 'v2@test.gob.bo'
    assert data['first_name'] == 'V2'
    assert data['roles'] == [
        {'codigo': 'superadmin', 'nombre': 'Superadministrador'}
    ]
    # Capacidades y alcances se completan en WP-03 (IAM)
    assert data['capabilities'] == []
    assert data['alcances'] == []


def test_me_retrieve_es_equivalente_al_list(auth_client_v2):
    list_data = auth_client_v2.get('/api/v2/me/').json()
    detail_data = auth_client_v2.get('/api/v2/me/me/').json()
    assert detail_data == list_data


@pytest.mark.parametrize('namespace', ['platform', 'sis-pe', 'sis-poa', 'sis-pro'])
def test_namespaces_v2_responden(auth_client_v2, namespace):
    """Los namespaces existen y responden (vacíos mientras no haya rutas)."""
    response = auth_client_v2.get(f'/api/v2/{namespace}/')
    assert response.status_code == 200
    assert response.json() == {}


def test_schema_v2_exporta_openapi(auth_client_v2):
    response = auth_client_v2.get('/api/v2/schema/', HTTP_ACCEPT='application/json')
    assert response.status_code == 200
    data = response.json()
    assert data['info']['version'] == '2.0.0'
    # Solo paths V2 (ADR-002)
    assert '/api/v2/me/' in data['paths']
    assert all(p.startswith('/api/v2/') for p in data['paths'])


def test_api_v1_sigue_intacta(usuario_v2):
    """No-regresión: V1 no fue retirada ni alterada (ADR-002)."""
    client = APIClient()
    anon = client.get('/api/v1/')
    assert anon.status_code == 401

    auth = APIClient()
    auth.force_authenticate(user=usuario_v2)
    response = auth.get('/api/v1/')
    assert response.status_code == 200
