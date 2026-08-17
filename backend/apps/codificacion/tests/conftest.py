"""Fixtures compartidos para los tests de la app codificacion."""
import datetime

import pytest

from apps.codificacion.models import VersionCatalogoPlan
from apps.gestion.models import GestionFiscal
from apps.planificacion.models import Plan


@pytest.fixture
def gestion_fiscal_2027(db):
    """Gestión fiscal 2027 (FK de SecuenciaCodigo/Homologacion/...)."""
    return GestionFiscal.objects.get_or_create(
        anio=2027, defaults={'estado': 'abierta'},
    )[0]


@pytest.fixture
def gestion_fiscal_2028(db):
    """Gestión fiscal 2028 (FK; usada por tests de reinicio por gestión)."""
    return GestionFiscal.objects.get_or_create(
        anio=2028, defaults={'estado': 'abierta'},
    )[0]


@pytest.fixture
def crear_plan(db):
    """Factory de planes de prueba (unicidad por (codigo, tipo))."""
    def _crear(codigo='PLAN-TEST', tipo='pgdesa'):
        return Plan.objects.create(
            codigo=codigo,
            nombre='Plan de prueba',
            tipo=tipo,
            gestion_inicio=2026,
            gestion_fin=2030,
            fecha_vigencia_desde=datetime.date(2026, 1, 1),
        )
    return _crear


@pytest.fixture
def version_catalogo(crear_plan):
    """Versión de catálogo en borrador sobre un plan PGDESA de prueba."""
    plan = crear_plan(codigo='PGDESA-TEST', tipo='pgdesa')
    return VersionCatalogoPlan.objects.create(plan=plan, gestion=2026)


@pytest.fixture
def version_pad(crear_plan):
    """Versión de catálogo en borrador sobre un plan municipal (PAD)."""
    plan = crear_plan(codigo='PAD-TEST', tipo='municipal')
    return VersionCatalogoPlan.objects.create(plan=plan, gestion=2026)
