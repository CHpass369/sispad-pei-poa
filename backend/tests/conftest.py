"""
Fixtures compartidas para todos los tests de SISPOA.
"""
import pytest
from datetime import date
from decimal import Decimal
from django.test import override_settings
from rest_framework.test import APIClient
from apps.accounts.models import Usuario, Rol
from apps.gestion.models import GestionFiscal
from apps.catalogos.models import (
    ObjetoGasto, FuenteFinanciamiento, OrganismoFinanciador,
    UnidadMedida
)
from apps.organizacion.models import (
    TipoUnidad, UnidadOrganizacional, DireccionAdministrativa,
    UnidadEjecutora
)
from apps.presupuesto.models import ProgramaPresupuestario
from apps.normativa.models import ReglaPresupuestariaLegal
from apps.planificacion.models import Plan, NodoPlanificacion, AccionMedianoPlazo


@pytest.fixture(autouse=True)
def override_db_settings(settings):
    """Usa la misma base de datos PostGIS para tests (no sqlite)."""
    pass


@pytest.fixture
def api_client():
    """Cliente DRF sin autenticar."""
    return APIClient()


@pytest.fixture
def admin_user(db):
    """Usuario superadmin autenticado."""
    user, _ = Usuario.objects.get_or_create(
        email='test_admin@gamsacaba.gob.bo',
        defaults={
            'first_name': 'Test', 'last_name': 'Admin',
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
def gestion(db):
    """Gestión fiscal 2026."""
    g, _ = GestionFiscal.objects.get_or_create(
        anio=2026,
        defaults={
            'estado': 'preparacion',
            'anio_inicio_plurianual': 2026,
            'anio_fin_plurianual': 2028,
        }
    )
    return g


@pytest.fixture
def fuentes(db):
    """Fuentes de financiamiento básicas."""
    vig = date(2026, 1, 1)
    FuenteFinanciamiento.objects.get_or_create(
        codigo='41-113', gestion=2026,
        defaults={'denominacion': 'CT - Coparticipación Tributaria',
                  'fecha_vigencia_desde': vig}
    )
    FuenteFinanciamiento.objects.get_or_create(
        codigo='20-210', gestion=2026,
        defaults={'denominacion': 'RE - Recursos Específicos',
                  'fecha_vigencia_desde': vig}
    )
    FuenteFinanciamiento.objects.get_or_create(
        codigo='41-119', gestion=2026,
        defaults={'denominacion': 'IDH - Impuesto Directo a Hidrocarburos',
                  'fecha_vigencia_desde': vig}
    )
    return FuenteFinanciamiento.objects.filter(gestion=2026)


@pytest.fixture
def objetos_gasto(db):
    """Objetos del gasto básicos."""
    vig = date(2026, 1, 1)
    ObjetoGasto.objects.get_or_create(
        codigo='10000', gestion=2026,
        defaults={'denominacion': 'SERVICIOS PERSONALES',
                  'fecha_vigencia_desde': vig}
    )
    ObjetoGasto.objects.get_or_create(
        codigo='20000', gestion=2026,
        defaults={'denominacion': 'SERVICIOS NO PERSONALES',
                  'fecha_vigencia_desde': vig}
    )
    return ObjetoGasto.objects.filter(gestion=2026)


@pytest.fixture
def unidades_medida(db):
    vig = date(2026, 1, 1)
    UnidadMedida.objects.get_or_create(
        codigo='UN', gestion=2026,
        defaults={'denominacion': 'Unidad', 'fecha_vigencia_desde': vig}
    )
    return UnidadMedida.objects.filter(gestion=2026)


@pytest.fixture
def programa(db):
    p, _ = ProgramaPresupuestario.objects.get_or_create(
        codigo='000', gestion=2026,
        defaults={'nombre': 'FUNCIONAMIENTO ALCALDIA MUNICIPAL'}
    )
    return p


@pytest.fixture
def reglas(db):
    """Reglas presupuestarias para tests."""
    reglas_data = [
        {
            'codigo': 'limite_gasto_funcionamiento',
            'nombre': 'Límite gasto funcionamiento',
            'descripcion': 'Límite del 60% para gastos de funcionamiento',
            'tipo': 'limite', 'severidad': 'bloqueante',
            'parametros': {'porcentaje': 0.60},
            'gestion_desde': 2024,
            'mensaje': 'El gasto de funcionamiento supera el límite legal',
        },
        {
            'codigo': 'no_superar_techo',
            'nombre': 'No superar techo',
            'descripcion': 'El formulado no puede superar el techo asignado',
            'tipo': 'limite', 'severidad': 'bloqueante',
            'parametros': {},
            'gestion_desde': 2024,
            'mensaje': 'Monto formulado supera techo asignado',
        },
        {
            'codigo': 'gasto_sus',
            'nombre': 'Asignación SUS',
            'descripcion': 'Asignación mínima del 10% para SUS',
            'tipo': 'minimo', 'severidad': 'bloqueante',
            'parametros': {'porcentaje': 0.10},
            'gestion_desde': 2024,
            'mensaje': 'Asignación SUS inferior al mínimo',
        },
        {
            'codigo': 'renta_dignidad',
            'nombre': 'Renta Dignidad',
            'descripcion': 'Aporte mínimo del 0.75% para Renta Dignidad',
            'tipo': 'minimo', 'severidad': 'bloqueante',
            'parametros': {'porcentaje': 0.0075},
            'gestion_desde': 2024,
            'mensaje': 'Aporte Renta Dignidad inferior',
        },
        {
            'codigo': 'seguridad_ciudadana',
            'nombre': 'Seguridad Ciudadana',
            'descripcion': 'Asignación mínima del 10% para seguridad ciudadana',
            'tipo': 'minimo', 'severidad': 'bloqueante',
            'parametros': {'porcentaje': 0.10},
            'gestion_desde': 2024,
            'mensaje': 'Asignación seguridad ciudadana inferior',
        },
        {
            'codigo': 'consistencia_anual_plurianual',
            'nombre': 'Consistencia anual/plurianual',
            'descripcion': 'Consistencia entre presupuesto anual y plurianual',
            'tipo': 'consistencia', 'severidad': 'advertencia',
            'parametros': {'tolerancia': 0.05},
            'gestion_desde': 2024,
            'mensaje': 'Diferencia anual vs plurianual',
        },
    ]
    for r in reglas_data:
        ReglaPresupuestariaLegal.objects.get_or_create(
            codigo=r['codigo'], defaults=r
        )
    return ReglaPresupuestariaLegal.objects.filter(activo=True)


@pytest.fixture
def plan_pei(db):
    p, _ = Plan.objects.get_or_create(
        codigo='PEI-TEST', tipo='pei',
        defaults={
            'nombre': 'PEI Test',
            'gestion_inicio': 2021, 'gestion_fin': 2025,
            'fecha_vigencia_desde': date(2021, 1, 1),
        }
    )
    return p


@pytest.fixture
def nodo_amp(plan_pei, db):
    nodo, _ = NodoPlanificacion.objects.get_or_create(
        plan=plan_pei, nivel='accion_mediano',
        codigo='AMP-TEST-001', gestion=2025,
        defaults={'nombre': 'Acción de mediano plazo test'}
    )
    amp, _ = AccionMedianoPlazo.objects.get_or_create(
        codigo='AMP-TEST-001',
        defaults={
            'nombre': 'AMP Test',
            'nodo_planificacion': nodo,
            'gestion_inicio': 2021, 'gestion_fin': 2025,
        }
    )
    return amp


@pytest.fixture
def unidad_organizacional(db):
    tipo, _ = TipoUnidad.objects.get_or_create(
        codigo='SEC-TEST', defaults={'nombre': 'Secretaría Test', 'nivel': 1}
    )
    u, _ = UnidadOrganizacional.objects.get_or_create(
        codigo='TEST-SEC', gestion=2026,
        defaults={
            'nombre': 'Secretaría de Test',
            'sigla': 'TEST',
            'tipo': tipo,
            'fecha_vigencia_desde': date(2026, 1, 1),
        }
    )
    return u
