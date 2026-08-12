"""
Tests de la API V2 de techos (fixes K3/K4 de la 4R, slice S2).

Router LOCAL (este módulo define su propio urlpatterns): evita depender de
config/urls_v2.py, que en el working tree tiene el swap poau→sis_poa del
branch hermano (no se toca). Con `@pytest.mark.urls` pytest-django usa esta
URLconf como ROOT_URLCONF del test.

- K3: TechoSerializerV2 create funcional (gestion_fiscal writable,
  monto_total read_only, decimales como strings, monto_distribuido == motor).
- K4: lectura exige una capacidad de CAPACIDADES_LECTURA (403 sin ella,
  200 con sis_poa.project.read) en techos, recursos y gastos obligatorios.
"""
from datetime import date
from decimal import Decimal

import pytest
from django.urls import include, path
from rest_framework import status
from rest_framework.routers import DefaultRouter
from rest_framework.test import APIClient

from apps.accounts.models import Capacidad, Rol, Usuario
from apps.catalogos.models import FuenteFinanciamiento, OrganismoFinanciador
from apps.gestion.models import GestionFiscal
from apps.techos.models import DistribucionTecho, TechoPresupuestario
from apps.techos.services import budget_service
from apps.techos.views_v2 import (
    GastoObligatorioViewSetV2,
    RecursoTechoViewSetV2,
    TechoViewSetV2,
)

_router = DefaultRouter()
_router.register('techos', TechoViewSetV2, basename='v2-test-techos')
_router.register(
    'techo-recursos', RecursoTechoViewSetV2, basename='v2-test-techo-recursos',
)
_router.register(
    'techo-gastos-obligatorios', GastoObligatorioViewSetV2,
    basename='v2-test-techo-gastos-obligatorios',
)

urlpatterns = [
    path('', include(_router.urls)),
]

URLS = 'apps.techos.tests.test_api_v2_techos'


@pytest.fixture
def base(db):
    """Techo 1:1 con jerarquía sintética: categoría 450/20 + hoja 450/20."""
    vig = date(2026, 1, 1)
    fuente = FuenteFinanciamiento.objects.create(
        codigo='41-113', gestion=2026,
        denominacion='Coparticipación Tributaria', fecha_vigencia_desde=vig,
    )
    organismo = OrganismoFinanciador.objects.create(
        codigo='GOB-MUN', gestion=2026,
        denominacion='Gobierno Municipal', fecha_vigencia_desde=vig,
    )
    gestion = GestionFiscal.objects.create(anio=2026, estado='preparacion')
    techo = TechoPresupuestario.objects.create(
        gestion=2026, gestion_fiscal=gestion, monto_total=Decimal('1000.00'),
        fuente=fuente, organismo=organismo,
    )
    categoria = DistribucionTecho.objects.create(
        techo=techo, concepto='MIGRACION LEGACY 0004',
        monto_asignado=Decimal('450.00'), monto_reserva=Decimal('20.00'),
        activo=True, version=1,
    )
    DistribucionTecho.objects.create(
        techo=techo, padre=categoria, monto_asignado=Decimal('450.00'),
        monto_reserva=Decimal('20.00'), activo=True, version=1,
    )
    return {
        'fuente': fuente, 'organismo': organismo,
        'gestion': gestion, 'techo': techo,
    }


@pytest.fixture
def usuario_lector(db):
    """Usuario con SOLO la capacidad sis_poa.project.read (design §11)."""
    user = Usuario.objects.create_user(
        email='lector_techos@gamsacaba.gob.bo', password='test123',
    )
    cap, _ = Capacidad.objects.get_or_create(
        codigo='sis_poa.project.read',
        defaults={
            'nombre': 'Leer presupuesto del proyecto', 'sistema': 'sis-poa',
            'orden': 30,
        },
    )
    rol = Rol.objects.create(codigo='lector_techos', nombre='Lector de techos')
    rol.capacidades.add(cap)
    user.roles.add(rol)
    return user


@pytest.fixture
def usuario_sin_capacidad(db):
    """Usuario autenticado sin ninguna capacidad de lectura financiera."""
    return Usuario.objects.create_user(
        email='sin_capacidad@gamsacaba.gob.bo', password='test123',
    )


@pytest.fixture
def usuario_escritor(db):
    """Usuario con sis_poa.budget.manage (CAPACIDADES_ESCRITURA)."""
    user = Usuario.objects.create_user(
        email='escritor_techos@gamsacaba.gob.bo', password='test123',
    )
    cap, _ = Capacidad.objects.get_or_create(
        codigo='sis_poa.budget.manage',
        defaults={
            'nombre': 'Gestionar presupuesto', 'sistema': 'sis-poa', 'orden': 12,
        },
    )
    rol = Rol.objects.create(codigo='escritor_techos', nombre='Escritor de techos')
    rol.capacidades.add(cap)
    user.roles.add(rol)
    return user


def _client(usuario):
    client = APIClient()
    client.force_authenticate(user=usuario)
    return client


def _payload_techo(base, **extra):
    """Payload de POST /techos/ con una GestionFiscal NUEVA (el fixture ya
    ocupa la 1:1 de su gestión; anio es unique)."""
    gestion = GestionFiscal.objects.create(anio=2027, estado='preparacion')
    payload = {
        'gestion': 2027,
        'gestion_fiscal': str(gestion.id),
        'fuente': str(base['fuente'].id),
        'organismo': str(base['organismo'].id),
    }
    payload.update(extra)
    return payload


# ---------------------------------------------------------------------------
# K3 — serializer V2: create con gestion_fiscal, monto_total read_only,
# decimales como strings y monto_distribuido == motor
# ---------------------------------------------------------------------------

@pytest.mark.urls(URLS)
@pytest.mark.django_db
def test_k3_create_con_gestion_fiscal_201(base, usuario_escritor):
    """POST /techos/ con gestion_fiscal → 201 (create INTENCIONAL, §12)."""
    client = _client(usuario_escritor)
    resp = client.post('/techos/', _payload_techo(base), format='json')
    assert resp.status_code == status.HTTP_201_CREATED, resp.data
    assert resp.data['gestion'] == 2027
    assert resp.data['monto_total'] == '0.00'
    assert TechoPresupuestario.objects.filter(gestion=2027).count() == 1


@pytest.mark.urls(URLS)
@pytest.mark.django_db
def test_k3_create_sin_gestion_fiscal_400(base, usuario_escritor):
    """POST /techos/ sin gestion_fiscal → 400 (campo requerido, NOT NULL)."""
    client = _client(usuario_escritor)
    resp = client.post('/techos/', {
        'gestion': 2027,
        'fuente': str(base['fuente'].id),
    }, format='json')
    assert resp.status_code == status.HTTP_400_BAD_REQUEST
    # El api_exception_handler envuelve los errores en {'error': ..., ...}.
    assert 'gestion_fiscal' in resp.data['error']


@pytest.mark.urls(URLS)
@pytest.mark.django_db
def test_k3_monto_total_no_escribible(base, usuario_escritor):
    """monto_total es read_only (Q1/DD6): el valor enviado se ignora."""
    client = _client(usuario_escritor)
    resp = client.post(
        '/techos/',
        _payload_techo(base, monto_total='12345678.00'),
        format='json',
    )
    assert resp.status_code == status.HTTP_201_CREATED, resp.data
    techo = TechoPresupuestario.objects.get(pk=resp.data['id'])
    # La columna legacy nace en 0 (create() setdefault): nunca toma el
    # valor del cliente.
    assert techo.monto_total == Decimal('0.00')


@pytest.mark.urls(URLS)
@pytest.mark.django_db
def test_k3_lista_decimales_como_strings_y_monto_distribuido_motor(
    base, usuario_lector,
):
    """GET /techos/ → decimales como strings y monto_distribuido == motor."""
    client = _client(usuario_lector)
    resp = client.get('/techos/')
    assert resp.status_code == status.HTTP_200_OK
    techo_data = next(
        t for t in resp.data['results'] if t['id'] == str(base['techo'].id)
    )
    motor = budget_service.get_distributed(base['techo'])
    assert techo_data['monto_distribuido'] == str(motor) == '450.00'
    assert isinstance(techo_data['monto_distribuido'], str)
    assert techo_data['saldo_disponible'] == '530.00'
    assert isinstance(techo_data['total_recursos'], str)


@pytest.mark.urls(URLS)
@pytest.mark.django_db
def test_k3_detalle_decimales_como_strings(base, usuario_lector):
    """GET /techos/{id}/ → decimales como strings (sin N+1 en detail)."""
    client = _client(usuario_lector)
    resp = client.get(f"/techos/{base['techo'].id}/")
    assert resp.status_code == status.HTTP_200_OK
    assert resp.data['monto_distribuido'] == '450.00'
    assert resp.data['saldo_disponible'] == '530.00'


# ---------------------------------------------------------------------------
# K4 — lectura exige CAPACIDADES_LECTURA (design §11)
# ---------------------------------------------------------------------------

@pytest.mark.urls(URLS)
@pytest.mark.django_db
def test_k4_sin_capacidad_403_lista_techos(base, usuario_sin_capacidad):
    """Autenticado sin capacidad de lectura → 403 (no IsAuthenticated)."""
    client = _client(usuario_sin_capacidad)
    resp = client.get('/techos/')
    assert resp.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.urls(URLS)
@pytest.mark.django_db
def test_k4_sin_capacidad_403_retrieve_y_actions(base, usuario_sin_capacidad):
    """retrieve, resumen y control_distribucion también exigen lectura."""
    client = _client(usuario_sin_capacidad)
    assert client.get(f"/techos/{base['techo'].id}/").status_code == 403
    assert client.get(f"/techos/{base['techo'].id}/resumen/").status_code == 403
    assert (
        client.get(
            f"/techos/{base['techo'].id}/control_distribucion/?monto=100",
        ).status_code == 403
    )


@pytest.mark.urls(URLS)
@pytest.mark.django_db
def test_k4_con_project_read_200(base, usuario_lector):
    """Usuario con sis_poa.project.read → 200 en list y detalle."""
    client = _client(usuario_lector)
    assert client.get('/techos/').status_code == 200
    assert client.get(f"/techos/{base['techo'].id}/").status_code == 200
    assert client.get(f"/techos/{base['techo'].id}/resumen/").status_code == 200


@pytest.mark.urls(URLS)
@pytest.mark.django_db
def test_k4_recursos_y_gastos_obligatorios_mismo_permiso(
    base, usuario_lector, usuario_sin_capacidad,
):
    """RecursoTechoViewSetV2 y GastoObligatorioViewSetV2 aplican lectura."""
    client_ok = _client(usuario_lector)
    assert client_ok.get('/techo-recursos/').status_code == 200
    assert client_ok.get('/techo-gastos-obligatorios/').status_code == 200

    client_no = _client(usuario_sin_capacidad)
    assert client_no.get('/techo-recursos/').status_code == 403
    assert client_no.get('/techo-gastos-obligatorios/').status_code == 403
