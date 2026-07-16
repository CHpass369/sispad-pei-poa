"""
Tests de API REST: endpoints críticos.
"""
import pytest
from rest_framework import status


class TestAuthAPI:
    """Autenticación JWT."""

    def test_login_exitoso(self, api_client, admin_user):
        """POST /auth/login/ con credenciales válidas."""
        resp = api_client.post('/api/v1/auth/login/', {
            'email': 'test_admin@gamsacaba.gob.bo',
            'password': 'test2026',
        }, format='json')
        assert resp.status_code == status.HTTP_200_OK
        assert 'access' in resp.data
        assert 'refresh' in resp.data

    def test_login_fallido(self, api_client, db):
        """POST /auth/login/ con credenciales inválidas."""
        resp = api_client.post('/api/v1/auth/login/', {
            'email': 'noexiste@gamsacaba.gob.bo',
            'password': 'wrong',
        }, format='json')
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_me_autenticado(self, auth_client, admin_user):
        """GET /auth/usuarios/me/ con token válido."""
        resp = auth_client.get('/api/v1/auth/usuarios/me/')
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data['email'] == 'test_admin@gamsacaba.gob.bo'

    def test_me_no_autenticado(self, api_client):
        """GET /auth/usuarios/me/ sin token."""
        resp = api_client.get('/api/v1/auth/usuarios/me/')
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED


class TestGestionAPI:
    """Endpoints de gestión fiscal."""

    def test_list_gestiones(self, auth_client, gestion):
        resp = auth_client.get('/api/v1/gestiones/')
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data['count'] >= 1
        assert any(g['anio'] == 2026 for g in resp.data['results'])

    def test_detalle_gestion(self, auth_client, gestion):
        resp = auth_client.get(f'/api/v1/gestiones/{gestion.id}/')
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data['anio'] == 2026


class TestCatalogosAPI:
    """Endpoints de catálogos."""

    def test_list_fuentes(self, auth_client, fuentes):
        resp = auth_client.get('/api/v1/fuentes/?gestion=2026')
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data['count'] >= 3

    def test_list_objetos_gasto(self, auth_client, objetos_gasto):
        resp = auth_client.get('/api/v1/objetos-gasto/?gestion=2026')
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data['count'] >= 2

    def test_list_unidades_medida(self, auth_client, unidades_medida):
        resp = auth_client.get('/api/v1/unidades-medida/?gestion=2026')
        assert resp.status_code == status.HTTP_200_OK


class TestOrganizacionAPI:
    """Endpoints de organización."""

    def test_unidades_arbol(self, auth_client, unidad_organizacional):
        resp = auth_client.get('/api/v1/unidades/arbol/')
        assert resp.status_code == status.HTTP_200_OK
        assert isinstance(resp.data, list)

    def test_list_programas(self, auth_client, programa):
        resp = auth_client.get('/api/v1/programas/?gestion=2026')
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data['count'] >= 1


class TestReglasAPI:
    """Endpoints de reglas presupuestarias."""

    def test_evaluar_reglas(self, auth_client, reglas):
        resp = auth_client.post('/api/v1/reglas-presupuestarias/evaluar/', {
            'gestion': 2026,
            'data': {
                'presupuesto_total': 10000000,
                'gasto_funcionamiento': 5000000,
                'techo_asignado': 5000000,
                'monto_formulado': 4800000,
                'asignacion_sus': 1200000,
                'asignacion_renta_dignidad': 80000,
                'asignacion_seguridad': 1100000,
            }
        }, format='json')
        assert resp.status_code == status.HTTP_200_OK
        assert isinstance(resp.data, list)
        assert len(resp.data) >= 3

    def test_evaluar_sin_gestion(self, auth_client):
        resp = auth_client.post('/api/v1/reglas-presupuestarias/evaluar/', {}, format='json')
        assert resp.status_code == status.HTTP_400_BAD_REQUEST


class TestPlanificacionAPI:
    """Endpoints de planificación."""

    def test_list_planes(self, auth_client, plan_pei):
        resp = auth_client.get('/api/v1/planes/')
        assert resp.status_code == status.HTTP_200_OK

    def test_list_acciones_mediano(self, auth_client, nodo_amp):
        resp = auth_client.get('/api/v1/acciones-mediano-plazo/')
        assert resp.status_code == status.HTTP_200_OK


class TestWorkflowAPI:
    """Endpoints de workflow."""

    def test_list_aprobaciones(self, auth_client):
        resp = auth_client.get('/api/v1/aprobaciones/')
        assert resp.status_code == status.HTTP_200_OK

    def test_list_observaciones(self, auth_client):
        resp = auth_client.get('/api/v1/observaciones/')
        assert resp.status_code == status.HTTP_200_OK

    def test_crear_observacion(self, auth_client):
        resp = auth_client.post('/api/v1/observaciones/', {
            'codigo': 'OBS-TEST-001',
            'tipo': 'tecnica',
            'severidad': 'moderada',
            'modulo': 'presupuesto',
            'registro_id': 'test-001',
            'texto': 'Observación de prueba',
            'gestion': 2026,
            'estado': 'abierta',
        }, format='json')
        assert resp.status_code == status.HTTP_201_CREATED
        assert resp.data['codigo'] == 'OBS-TEST-001'
