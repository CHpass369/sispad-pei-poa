"""
Fixtures compartidas para todos los tests de SISPOA.
"""
import pytest
from datetime import date
from decimal import Decimal
from django.conf import settings
from django.apps import apps as real_apps
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


@pytest.fixture
def api_client():
    """Cliente DRF sin autenticar."""
    return APIClient()


@pytest.fixture(autouse=True)
def _seeds_sqlite(db):
    """Siembra mínima SOLO para config.settings_test_sqlite.

    Ese settings crea el esquema directo desde los modelos (sin data
    migrations, porque SQLite no soporta los triggers plpgsql ni el
    catálogo geo). Para que los tests que presuponen catálogos siembren
    igual, se reutilizan las funciones seed de las propias data
    migrations (misma fuente, sin duplicar lógica). En PostgreSQL
    (config.settings) no hace nada: las migraciones ya sembraron.
    """
    if settings.SETTINGS_MODULE != 'config.settings_test_sqlite':
        return
    from importlib import import_module
    # Workflow: definición 'validacion_instrumento' + pasos (WP-08).
    import_module(
        'apps.workflow.migrations.'
        '0002_workflowdefinition_workflowstepdefinition_and_more'
    ).seed_definiciones(real_apps, None)
    # IAM: catálogo de capacidades + mapeo por rol (WP-03 / ADR-003).
    import_module(
        'apps.accounts.migrations.'
        '0002_capacidad_alcanceorganizacional_rol_capacidades'
    ).seed_capacidades(real_apps, None)


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
def fuentes(db, gestion):
    """Fuentes de financiamiento básicas."""
    vig = date(2026, 1, 1)
    FuenteFinanciamiento.objects.get_or_create(
        codigo='41-113', gestion=gestion,
        defaults={'denominacion': 'CT - Coparticipación Tributaria',
                  'fecha_vigencia_desde': vig}
    )
    FuenteFinanciamiento.objects.get_or_create(
        codigo='20-210', gestion=gestion,
        defaults={'denominacion': 'RE - Recursos Específicos',
                  'fecha_vigencia_desde': vig}
    )
    FuenteFinanciamiento.objects.get_or_create(
        codigo='41-119', gestion=gestion,
        defaults={'denominacion': 'IDH - Impuesto Directo a Hidrocarburos',
                  'fecha_vigencia_desde': vig}
    )
    return FuenteFinanciamiento.objects.filter(gestion=gestion)


@pytest.fixture
def objetos_gasto(db, gestion):
    """Objetos del gasto básicos."""
    vig = date(2026, 1, 1)
    ObjetoGasto.objects.get_or_create(
        codigo='10000', gestion=gestion,
        defaults={'denominacion': 'SERVICIOS PERSONALES',
                  'fecha_vigencia_desde': vig}
    )
    ObjetoGasto.objects.get_or_create(
        codigo='20000', gestion=gestion,
        defaults={'denominacion': 'SERVICIOS NO PERSONALES',
                  'fecha_vigencia_desde': vig}
    )
    return ObjetoGasto.objects.filter(gestion=gestion)


@pytest.fixture
def unidades_medida(db, gestion):
    vig = date(2026, 1, 1)
    UnidadMedida.objects.get_or_create(
        codigo='UN', gestion=gestion,
        defaults={'denominacion': 'Unidad', 'fecha_vigencia_desde': vig}
    )
    return UnidadMedida.objects.filter(gestion=gestion)


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
def unidad_organizacional(db, gestion):
    tipo, _ = TipoUnidad.objects.get_or_create(
        codigo='SEC-TEST', defaults={'nombre': 'Secretaría Test', 'nivel': 1}
    )
    u, _ = UnidadOrganizacional.objects.get_or_create(
        codigo='TEST-SEC', gestion=gestion,
        defaults={
            'nombre': 'Secretaría de Test',
            'sigla': 'TEST',
            'tipo': tipo,
            'fecha_vigencia_desde': date(2026, 1, 1),
        }
    )
    return u
