"""Tests de la API V1 de la app organizacion (PIP-CORE-004).

Cubren los contratos que consume el frontend (corregidos en PIP-CORE-001):

- GET  /api/v1/unidades-ejecutoras/            (urls.py:12)
- GET  /api/v1/direcciones-administrativas/    (urls.py:11)
- GET  /api/v1/unidades/arbol/                 (views.py:24-25)
- CRUD básico de los viewsets del router V1.

Patrón del repo: pytest-django + APIClient con force_authenticate (superadmin),
los fixtures se definen locales porque el conftest de backend/tests/ no alcanza
a apps/*. Settings: config.settings (PostgreSQL/PostGIS).
"""
import datetime

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.models import Usuario
from apps.organizacion.models import (
    TipoUnidad, UnidadOrganizacional, DireccionAdministrativa,
    UnidadEjecutora, AsignacionUsuarioUnidad,
)


@pytest.fixture
def api_client():
    """Cliente DRF sin autenticar."""
    return APIClient()


@pytest.fixture
def admin_user(db):
    """Usuario superadmin autenticado (mismo patrón que backend/tests/conftest.py)."""
    user, _ = Usuario.objects.get_or_create(
        email='test_organizacion_admin@gamsacaba.gob.bo',
        defaults={
            'first_name': 'Test', 'last_name': 'Organizacion',
            'is_staff': True, 'is_superuser': True,
        }
    )
    user.set_password('test2026')
    user.save()
    return user


@pytest.fixture
def auth_client(admin_user):
    """Cliente DRF autenticado como superadmin."""
    client = APIClient()
    client.force_authenticate(user=admin_user)
    return client


@pytest.fixture
def tipo_unidad(db):
    return TipoUnidad.objects.create(
        codigo='SEC', nombre='Secretaría', nivel=1,
    )


@pytest.fixture
def tipo_direccion(db):
    return TipoUnidad.objects.create(
        codigo='DIR', nombre='Dirección', nivel=2,
    )


@pytest.fixture
def unidad(db, tipo_unidad):
    return UnidadOrganizacional.objects.create(
        codigo='SEC-001', nombre='Secretaría de Test', sigla='SEC',
        tipo=tipo_unidad, gestion=2026,
        fecha_vigencia_desde=datetime.date(2026, 1, 1),
    )


@pytest.fixture
def unidad_hija(db, unidad, tipo_direccion):
    return UnidadOrganizacional.objects.create(
        codigo='DIR-001', nombre='Dirección de Test', sigla='DIR',
        tipo=tipo_direccion, padre=unidad, gestion=2026,
        fecha_vigencia_desde=datetime.date(2026, 1, 1),
    )


@pytest.fixture
def da(db):
    return DireccionAdministrativa.objects.create(
        codigo='DA01', nombre='Dirección Administrativa 01', gestion=2026,
        fecha_vigencia_desde=datetime.date(2026, 1, 1),
    )


@pytest.fixture
def ue(db, da, unidad):
    return UnidadEjecutora.objects.create(
        codigo='UE01', nombre='Unidad Ejecutora 01',
        da=da, unidad_organizacional=unidad, gestion=2026,
        fecha_vigencia_desde=datetime.date(2026, 1, 1),
    )


# =============================================================================
# Contrato de URLs V1 (PIP-CORE-001: sin doble prefijo)
# =============================================================================

class TestContratoURLsV1:
    """reverse() debe resolver a /api/v1/... (el doble prefijo sería un fallo)."""

    def test_url_unidades_ejecutoras(self):
        assert reverse('unidadejecutora-list') == '/api/v1/unidades-ejecutoras/'

    def test_url_direcciones_administrativas(self):
        assert reverse('direccionadministrativa-list') == '/api/v1/direcciones-administrativas/'

    def test_url_unidades_arbol(self):
        assert reverse('unidadorganizacional-arbol') == '/api/v1/unidades/arbol/'

    def test_url_unidades_list(self):
        assert reverse('unidadorganizacional-list') == '/api/v1/unidades/'


# =============================================================================
# Autenticación requerida (default: IsAuthenticated)
# =============================================================================

class TestAutenticacion:
    """Los endpoints exigen autenticación."""

    def test_unidades_ejecutoras_requiere_auth(self, api_client):
        assert api_client.get(reverse('unidadejecutora-list')).status_code == status.HTTP_401_UNAUTHORIZED

    def test_arbol_requiere_auth(self, api_client):
        assert api_client.get(reverse('unidadorganizacional-arbol')).status_code == status.HTTP_401_UNAUTHORIZED

    def test_direcciones_requiere_auth(self, api_client):
        assert api_client.get(reverse('direccionadministrativa-list')).status_code == status.HTTP_401_UNAUTHORIZED


# =============================================================================
# Unidades Ejecutoras (urls.py:12)
# =============================================================================

class TestUnidadEjecutoraAPI:
    """CRUD + shape de /api/v1/unidades-ejecutoras/."""

    def test_list_200_y_shape(self, auth_client, ue):
        resp = auth_client.get(reverse('unidadejecutora-list'))
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data['count'] == 1
        item = resp.data['results'][0]
        assert item['id'] == str(ue.id)
        assert item['codigo'] == 'UE01'
        assert item['nombre'] == 'Unidad Ejecutora 01'
        assert str(item['da']) == str(ue.da_id)
        assert str(item['unidad_organizacional']) == str(ue.unidad_organizacional_id)
        assert item['gestion'] == 2026
        assert item['activo'] is True
        assert item['fecha_vigencia_desde'] == '2026-01-01'
        assert item['fecha_vigencia_hasta'] is None
        assert 'created_at' in item and 'updated_at' in item

    def test_list_filtro_gestion(self, auth_client, ue):
        resp = auth_client.get(reverse('unidadejecutora-list'), {'gestion': 2027})
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data['count'] == 0

    def test_retrieve_200(self, auth_client, ue):
        resp = auth_client.get(reverse('unidadejecutora-detail', args=[ue.id]))
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data['codigo'] == 'UE01'

    def test_retrieve_404(self, auth_client):
        import uuid
        resp = auth_client.get(reverse('unidadejecutora-detail', args=[uuid.uuid4()]))
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    def test_create_201(self, auth_client, da):
        resp = auth_client.post(reverse('unidadejecutora-list'), {
            'codigo': 'UE02', 'nombre': 'Unidad Ejecutora 02',
            'da': str(da.id), 'gestion': 2026,
            'fecha_vigencia_desde': '2026-01-01',
        }, format='json')
        assert resp.status_code == status.HTTP_201_CREATED
        assert resp.data['codigo'] == 'UE02'
        assert str(resp.data['da']) == str(da.id)

    def test_create_400_sin_da(self, auth_client):
        resp = auth_client.post(reverse('unidadejecutora-list'), {
            'codigo': 'UE03', 'nombre': 'Sin DA', 'gestion': 2026,
            'fecha_vigencia_desde': '2026-01-01',
        }, format='json')
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_update_200(self, auth_client, ue):
        resp = auth_client.patch(
            reverse('unidadejecutora-detail', args=[ue.id]),
            {'nombre': 'Unidad Ejecutora Renombrada'}, format='json',
        )
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data['nombre'] == 'Unidad Ejecutora Renombrada'

    def test_delete_204(self, auth_client, ue):
        resp = auth_client.delete(reverse('unidadejecutora-detail', args=[ue.id]))
        assert resp.status_code == status.HTTP_204_NO_CONTENT
        assert UnidadEjecutora.objects.filter(pk=ue.id).exists() is False


# =============================================================================
# Direcciones Administrativas (urls.py:11)
# =============================================================================

class TestDireccionAdministrativaAPI:
    """CRUD + shape de /api/v1/direcciones-administrativas/."""

    def test_list_200_y_shape(self, auth_client, da):
        resp = auth_client.get(reverse('direccionadministrativa-list'))
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data['count'] == 1
        item = resp.data['results'][0]
        assert item['id'] == str(da.id)
        assert item['codigo'] == 'DA01'
        assert item['nombre'] == 'Dirección Administrativa 01'
        assert item['gestion'] == 2026
        assert item['activo'] is True
        assert item['fecha_vigencia_desde'] == '2026-01-01'

    def test_create_201(self, auth_client):
        resp = auth_client.post(reverse('direccionadministrativa-list'), {
            'codigo': 'DA02', 'nombre': 'Dirección Administrativa 02',
            'gestion': 2026, 'fecha_vigencia_desde': '2026-01-01',
        }, format='json')
        assert resp.status_code == status.HTTP_201_CREATED
        assert resp.data['codigo'] == 'DA02'

    def test_create_400_sin_codigo(self, auth_client):
        resp = auth_client.post(reverse('direccionadministrativa-list'), {
            'nombre': 'Sin código', 'gestion': 2026,
            'fecha_vigencia_desde': '2026-01-01',
        }, format='json')
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_update_200(self, auth_client, da):
        resp = auth_client.patch(
            reverse('direccionadministrativa-detail', args=[da.id]),
            {'nombre': 'DA Renombrada'}, format='json',
        )
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data['nombre'] == 'DA Renombrada'

    def test_delete_204(self, auth_client, da):
        resp = auth_client.delete(reverse('direccionadministrativa-detail', args=[da.id]))
        assert resp.status_code == status.HTTP_204_NO_CONTENT


# =============================================================================
# Árbol de unidades (views.py:24-25)
# =============================================================================

class TestArbolUnidadesAPI:
    """GET /api/v1/unidades/arbol/ — estructura de árbol + filtro por gestión."""

    def test_arbol_200_con_estructura_anidada(self, auth_client, unidad, unidad_hija):
        resp = auth_client.get(reverse('unidadorganizacional-arbol'))
        assert resp.status_code == status.HTTP_200_OK
        assert isinstance(resp.data, list)
        assert len(resp.data) == 1
        root = resp.data[0]
        assert root['id'] == str(unidad.id)
        assert root['codigo'] == 'SEC-001'
        assert root['nombre'] == 'Secretaría de Test'
        assert root['sigla'] == 'SEC'
        assert root['gestion'] == 2026
        assert root['activo'] is True
        assert str(root['tipo']) == str(unidad.tipo_id)
        assert str(root['tipo_id']) == str(unidad.tipo_id)
        assert len(root['hijas']) == 1
        hijas = root['hijas'][0]
        assert hijas['id'] == str(unidad_hija.id)
        assert hijas['codigo'] == 'DIR-001'
        assert hijas['hijas'] == []

    def test_arbol_filtro_gestion(self, auth_client, tipo_unidad, unidad):
        otra = UnidadOrganizacional.objects.create(
            codigo='SEC-2027', nombre='Secretaría 2027', sigla='S27',
            tipo=tipo_unidad, gestion=2027,
            fecha_vigencia_desde=datetime.date(2027, 1, 1),
        )
        resp = auth_client.get(reverse('unidadorganizacional-arbol'), {'gestion': 2026})
        assert resp.status_code == status.HTTP_200_OK
        codigos = [r['codigo'] for r in resp.data]
        assert codigos == ['SEC-001']
        assert 'SEC-2027' not in codigos
        assert UnidadOrganizacional.objects.filter(codigo='SEC-2027').exists()

    def test_arbol_excluye_hijas_inactivas(self, auth_client, unidad, tipo_direccion):
        inactiva = UnidadOrganizacional.objects.create(
            codigo='DIR-X', nombre='Dirección Inactiva', sigla='DIX',
            tipo=tipo_direccion, padre=unidad, gestion=2026,
            fecha_vigencia_desde=datetime.date(2026, 1, 1), activo=False,
        )
        resp = auth_client.get(reverse('unidadorganizacional-arbol'))
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data[0]['hijas'] == []
        assert inactiva.id

    def test_arbol_solo_raices(self, auth_client, unidad, tipo_direccion):
        """Una hija nunca aparece como raíz; si la raíz se inactiva, queda vacío."""
        UnidadOrganizacional.objects.create(
            codigo='DIR-001', nombre='Dirección de Test', sigla='DIR',
            tipo=tipo_direccion, padre=unidad, gestion=2026,
            fecha_vigencia_desde=datetime.date(2026, 1, 1),
        )
        resp = auth_client.get(reverse('unidadorganizacional-arbol'))
        assert resp.status_code == status.HTTP_200_OK
        assert [r['codigo'] for r in resp.data] == ['SEC-001']
        unidad.activo = False
        unidad.save()
        resp = auth_client.get(reverse('unidadorganizacional-arbol'))
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data == []

    def test_arbol_sin_datos(self, auth_client):
        resp = auth_client.get(reverse('unidadorganizacional-arbol'))
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data == []


# =============================================================================
# Unidades organizacionales (listado paginado)
# =============================================================================

class TestUnidadOrganizacionalAPI:
    def test_list_200_paginado(self, auth_client, unidad):
        resp = auth_client.get(reverse('unidadorganizacional-list'))
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data['count'] == 1
        assert resp.data['results'][0]['codigo'] == 'SEC-001'

    def test_create_201(self, auth_client, tipo_unidad):
        resp = auth_client.post(reverse('unidadorganizacional-list'), {
            'codigo': 'SEC-002', 'nombre': 'Secretaría 002', 'sigla': 'S02',
            'tipo': str(tipo_unidad.id), 'gestion': 2026,
            'fecha_vigencia_desde': '2026-01-01',
        }, format='json')
        assert resp.status_code == status.HTTP_201_CREATED
        assert resp.data['codigo'] == 'SEC-002'


# =============================================================================
# Tipos de unidad y asignaciones usuario-unidad
# =============================================================================

class TestTiposUnidadAPI:
    def test_list_200(self, auth_client, tipo_unidad):
        resp = auth_client.get(reverse('tipounidad-list'))
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data['count'] == 1
        assert resp.data['results'][0]['codigo'] == 'SEC'


class TestAsignacionUsuarioUnidadAPI:
    def test_list_200(self, auth_client, admin_user, unidad):
        AsignacionUsuarioUnidad.objects.create(
            usuario=admin_user, unidad=unidad, gestion=2026,
        )
        resp = auth_client.get(reverse('asignacionusuariounidad-list'))
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data['count'] == 1
        item = resp.data['results'][0]
        assert str(item['usuario']) == str(admin_user.id)
        assert str(item['unidad']) == str(unidad.id)
