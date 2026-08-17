"""Contratos IAM V2 (WP-03 / ADR-003): capacidades, alcances y autorización."""
import pytest
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.models import AlcanceOrganizacional, Rol, Usuario
from apps.accounts.permissions import listar_capacidades, tiene_capacidad
from apps.organizacion.models import (
    TipoUnidad, UnidadOrganizacional,
)


@pytest.fixture
def rol_planificador(db):
    return Rol.objects.get(codigo='revisor_planificacion')


@pytest.fixture
def usuario_cap(rol_planificador, db):
    user = Usuario.objects.create_user(
        email='cap@test.gob.bo', password='test123',
    )
    user.roles.add(rol_planificador)
    return user


@pytest.fixture
def unidad(db):
    from datetime import date
    from apps.gestion.models import GestionFiscal
    tipo, _ = TipoUnidad.objects.get_or_create(
        codigo='SEC-TEST', defaults={'nombre': 'Secretaría Test', 'nivel': 1},
    )
    gestion_2026, _ = GestionFiscal.objects.get_or_create(
        anio=2026, defaults={'estado': 'preparacion'},
    )
    u, _ = UnidadOrganizacional.objects.get_or_create(
        codigo='SEC-CAP', gestion=gestion_2026,
        defaults={
            'nombre': 'Secretaría de Capacidades',
            'sigla': 'SECCAP',
            'tipo': tipo,
            'fecha_vigencia_desde': date(2026, 1, 1),
        },
    )
    return u


def test_listar_capacidades_de_rol_mapeado(usuario_cap):
    caps = listar_capacidades(usuario_cap)
    assert 'sis_pe.pad.validate' in caps
    assert 'sis_pe.instrumento.read' in caps
    # No hereda capacidades de otros roles
    assert 'platform.users.manage' not in caps


def test_superusuario_tiene_todas_las_capacidades(db):
    user = Usuario.objects.create_superuser(
        email='super@test.gob.bo', password='test123',
    )
    caps = listar_capacidades(user)
    assert len(caps) >= 20
    assert 'sis_pe.pad.edit' in caps
    assert 'platform.audit.read' in caps


def test_usuario_sin_roles_no_tiene_capacidades(db):
    user = Usuario.objects.create_user(email='anon@test.gob.bo', password='x')
    assert listar_capacidades(user) == []
    assert not tiene_capacidad(user, 'sis_pe.instrumento.read')


def test_tiene_capacidad_por_rol(usuario_cap):
    assert tiene_capacidad(usuario_cap, 'sis_pe.pad.validate')
    assert not tiene_capacidad(usuario_cap, 'sis_poa.budget.manage')


def test_capabilities_endpoint_rol_mapeado(usuario_cap):
    client = APIClient()
    client.force_authenticate(user=usuario_cap)
    response = client.get('/api/v2/me/capabilities/')
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data['usuario']['email'] == 'cap@test.gob.bo'
    assert data['roles'] == ['revisor_planificacion']
    assert 'sis_pe.pad.validate' in data['capabilities']
    assert data['alcances'] == []


def test_capabilities_endpoint_requiere_auth():
    response = APIClient().get('/api/v2/me/capabilities/')
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_alcances_organizacionales_incluidos(usuario_cap, unidad):
    AlcanceOrganizacional.objects.create(
        usuario=usuario_cap, unidad=unidad,
    )
    client = APIClient()
    client.force_authenticate(user=usuario_cap)
    data = client.get('/api/v2/me/capabilities/').json()
    assert len(data['alcances']) == 1
    alcance = data['alcances'][0]
    assert alcance['tipo'] == 'organizacional'
    assert alcance['unidad_id'] == str(unidad.id)
    assert alcance['unidad_nombre'] == 'Secretaría de Capacidades'


def test_alcance_inactivo_no_se_exporta(usuario_cap, unidad):
    AlcanceOrganizacional.objects.create(
        usuario=usuario_cap, unidad=unidad, activo=False,
    )
    client = APIClient()
    client.force_authenticate(user=usuario_cap)
    data = client.get('/api/v2/me/capabilities/').json()
    assert data['alcances'] == []


def test_tiene_capacidad_class_deniega_sin_rol(db):
    user = Usuario.objects.create_user(email='sinrol@test.gob.bo', password='x')
    assert not tiene_capacidad(user, 'sis_pe.instrumento.read')


def test_catalogo_capacidades_sembrado(db):
    from apps.accounts.models import Capacidad
    total = Capacidad.objects.count()
    assert total >= 20
    assert Capacidad.objects.filter(
        sistema='platform', activo=True
    ).count() >= 5
