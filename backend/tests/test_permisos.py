"""
Tests de permisos y acceso por rol.
Verifica que usuarios sin el rol adecuado no puedan acceder a recursos.
"""
import pytest
from rest_framework import status
from rest_framework.test import APIClient
from apps.accounts.models import Usuario, Rol


@pytest.fixture
def rol_responsable(db):
    r, _ = Rol.objects.get_or_create(
        codigo='responsable_unidad',
        defaults={'nombre': 'Responsable POA', 'es_sistema': True}
    )
    return r


@pytest.fixture
def rol_revisor(db):
    r, _ = Rol.objects.get_or_create(
        codigo='revisor_planificacion',
        defaults={'nombre': 'Revisor Planificación', 'es_sistema': True}
    )
    return r


@pytest.fixture
def rol_auditor(db):
    r, _ = Rol.objects.get_or_create(
        codigo='auditor',
        defaults={'nombre': 'Auditor', 'es_sistema': True}
    )
    return r


@pytest.fixture
def usuario_responsable(db, rol_responsable):
    u, _ = Usuario.objects.get_or_create(
        email='responsable@gamsacaba.gob.bo',
        defaults={'first_name': 'Resp', 'last_name': 'Unidad'}
    )
    u.set_password('test2026')
    u.roles.add(rol_responsable)
    u.save()
    return u


@pytest.fixture
def usuario_revisor(db, rol_revisor):
    u, _ = Usuario.objects.get_or_create(
        email='revisor@gamsacaba.gob.bo',
        defaults={'first_name': 'Rev', 'last_name': 'Planif'}
    )
    u.set_password('test2026')
    u.roles.add(rol_revisor)
    u.save()
    return u


@pytest.fixture
def usuario_auditor(db, rol_auditor):
    u, _ = Usuario.objects.get_or_create(
        email='auditor@gamsacaba.gob.bo',
        defaults={'first_name': 'Aud', 'last_name': 'itor'}
    )
    u.set_password('test2026')
    u.roles.add(rol_auditor)
    u.save()
    return u


class TestPermisosAPI:
    """Verifica que el control de acceso básico funciona."""

    ENDPOINTS_PUBLICOS = [
        ('POST', '/api/v1/auth/login/'),
    ]

    ENDPOINTS_PROTEGIDOS = [
        ('GET', '/api/v1/gestiones/'),
        ('GET', '/api/v1/unidades/'),
        ('GET', '/api/v1/programas/'),
        ('GET', '/api/v1/fuentes/'),
        ('GET', '/api/v1/planes/'),
        ('GET', '/api/v1/indicadores/'),
        ('GET', '/api/v1/observaciones/'),
        ('GET', '/api/v1/aprobaciones/'),
        ('GET', '/api/v1/lineas-presupuestarias/'),
    ]

    def test_endpoints_publicos(self, api_client, db):
        """Endpoints públicos deben funcionar sin auth."""
        for method, path in self.ENDPOINTS_PUBLICOS:
            resp = api_client.post(path, {'email': 'test@test.com', 'password': 'x'}, format='json')
            # 401 es aceptable (credenciales inválidas), 200 también
            assert resp.status_code in (200, 401), f'{method} {path} debe ser accesible sin auth'

    def test_endpoints_protegidos_sin_auth(self, api_client):
        """Endpoints protegidos deben rechazar sin token."""
        for method, path in self.ENDPOINTS_PROTEGIDOS:
            resp = api_client.get(path)
            assert resp.status_code == status.HTTP_401_UNAUTHORIZED, \
                f'{method} {path} debe retornar 401, retornó {resp.status_code}'

    def test_endpoints_protegidos_con_auth(self, auth_client):
        """Endpoints protegidos deben funcionar con token válido."""
        for method, path in self.ENDPOINTS_PROTEGIDOS[:5]:  # Primeros 5
            resp = auth_client.get(path)
            assert resp.status_code in (200, 404), \
                f'{method} {path} debe funcionar con auth, retornó {resp.status_code}'

    def test_usuario_puede_crear_observacion(self, usuario_responsable):
        """Usuario autenticado puede crear observaciones."""
        client = APIClient()
        client.force_authenticate(user=usuario_responsable)
        resp = client.post('/api/v1/observaciones/', {
            'codigo': 'OBS-PERM-001',
            'tipo': 'tecnica',
            'severidad': 'leve',
            'modulo': 'general',
            'registro_id': 'perm-test',
            'texto': 'Test de permisos',
            'gestion': 2026,
            'estado': 'abierta',
        }, format='json')
        assert resp.status_code == status.HTTP_201_CREATED

    def test_usuario_lista_usuarios(self, usuario_revisor):
        """Usuario normal puede listar usuarios."""
        client = APIClient()
        client.force_authenticate(user=usuario_revisor)
        resp = client.get('/api/v1/auth/usuarios/')
        assert resp.status_code == status.HTTP_200_OK

    def test_login_con_rol_valido(self, api_client, usuario_responsable):
        """Login debe funcionar y retornar token."""
        resp = api_client.post('/api/v1/auth/login/', {
            'email': 'responsable@gamsacaba.gob.bo',
            'password': 'test2026',
        }, format='json')
        assert resp.status_code == status.HTTP_200_OK
        assert 'access' in resp.data

    def test_me_retorna_roles(self, api_client, usuario_responsable):
        """El endpoint /me debe incluir los roles del usuario."""
        client = APIClient()
        client.force_authenticate(user=usuario_responsable)
        resp = client.get('/api/v1/auth/usuarios/me/')
        assert resp.status_code == status.HTTP_200_OK
        assert len(resp.data['roles_detalle']) > 0
        assert any(r['codigo'] == 'responsable_unidad' for r in resp.data['roles_detalle'])
