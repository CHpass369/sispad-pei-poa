"""
Pins de validar_techo (apps/sis_poa/migration_v2.py) — slice S1.

Estos tests importan modelos de apps.sis_poa, que solo está en
INSTALLED_APPS tras el swap poau→sis_poa del branch hermano. En HEAD
(commit slice sin el swap) el módulo se salta completo en colección.

Requiere apps.sis_poa en INSTALLED_APPS (swap poau→sis_poa del branch
hermano).
"""
from datetime import date
from decimal import Decimal

import pytest
from django.conf import settings

# Guard de colección en HEAD: si apps.sis_poa no está instalada, importar
# sus modelos levanta RuntimeError/AppRegistryNotReady (no ImportError), por
# eso se lee INSTALLED_APPS del settings directamente antes del importorskip.
if 'apps.sis_poa' not in settings.INSTALLED_APPS:
    pytest.skip(
        'Requiere apps.sis_poa en INSTALLED_APPS '
        '(swap poau→sis_poa del branch hermano)',
        allow_module_level=True,
    )
pytest.importorskip('apps.sis_poa.models')

from apps.catalogos.models import FuenteFinanciamiento  # noqa: E402
from apps.sis_poa.migration_v2 import validar_techo  # noqa: E402
from apps.sis_poa.models import (  # noqa: E402
    AccionCortoPlazo,
    Actividad,
    Operacion,
    PoAInstitucional,
    ProgramacionActividad,
)
from apps.techos.models import (  # noqa: E402
    DistribucionTecho,
    GastoObligatorio,
    RecursoTecho,
    TechoPresupuestario,
)

MONTO_RECURSOS = Decimal('245290497.00')
MONTO_GASTOS = Decimal('6464396.00')
MONTO_DISTRIBUIDO = Decimal('50000000.00')


@pytest.fixture
def fuente(db):
    return FuenteFinanciamiento.objects.create(
        codigo='41-113',
        gestion=2027,
        denominacion='Coparticipación Tributaria',
        fecha_vigencia_desde=date(2027, 1, 1),
    )


@pytest.fixture
def techo_2027(db, fuente):
    """Techo 2027 con recursos y gastos obligatorios de la ecuación pin."""
    techo = TechoPresupuestario.objects.create(
        gestion=2027,
        monto_total=MONTO_RECURSOS,
        fuente=fuente,
        concepto='Techo 2027',
    )
    RecursoTecho.objects.create(
        techo=techo, fuente=fuente,
        concepto='Coparticipación Tributaria', monto=Decimal('181658084.00'),
    )
    RecursoTecho.objects.create(
        techo=techo, fuente=fuente,
        concepto='Recursos Hipotecarios', monto=Decimal('63632413.00'),
    )
    GastoObligatorio.objects.create(
        techo=techo, fuente=fuente,
        denominacion='Renta Dignidad', monto=Decimal('3500000.00'),
    )
    GastoObligatorio.objects.create(
        techo=techo, fuente=fuente,
        denominacion='Seguridad Ciudadana', monto=Decimal('2964396.00'),
    )
    DistribucionTecho.objects.create(
        techo=techo, monto_asignado=MONTO_DISTRIBUIDO,
    )
    return techo


@pytest.fixture
def poa_2027(db):
    poa = PoAInstitucional.objects.create(
        gestion=2027, codigo='P-2027', nombre='POA 2027',
    )
    accion = AccionCortoPlazo.objects.create(
        poa=poa, codigo='ACP-01', nombre='Acción 1',
    )
    operacion = Operacion.objects.create(
        accion=accion, codigo='OP-01', nombre='Operación 1',
    )
    actividad = Actividad.objects.create(
        operacion=operacion, codigo='ACT-01', nombre='Actividad 1',
    )
    return poa, actividad


def _programar_financiero(actividad, monto):
    ProgramacionActividad.objects.create(
        actividad=actividad, anio=2027, tipo='financiera', programado=monto,
    )


# ---------------------------------------------------------------------------
# Pins validar_techo (migrados de test_ecuaciones.py, C2) + pins C3
# ---------------------------------------------------------------------------

def test_validar_techo_dentro_del_techo(techo_2027, poa_2027):
    poa, actividad = poa_2027
    _programar_financiero(actividad, Decimal('100000.00'))
    resultado = validar_techo(poa)
    assert resultado['excede'] is False
    assert resultado['techo'] == '245290497.00'
    assert resultado['formulado'] == '100000.00'


def test_validar_techo_excede(techo_2027, poa_2027):
    poa, actividad = poa_2027
    _programar_financiero(actividad, Decimal('300000000.00'))
    resultado = validar_techo(poa)
    assert resultado['excede'] is True
    assert resultado['techo'] == '245290497.00'
    assert resultado['formulado'] == '300000000.00'


def test_validar_techo_sin_techo_excede(poa_2027):
    """C3: gestión sin techos (techo 0.00) + formulado > 0 NO puede ser
    'dentro del techo': el guard `if techo and ...` se saltaba por falsy
    (Decimal('0.00')) y devolvía un falso OK."""
    poa, actividad = poa_2027
    _programar_financiero(actividad, Decimal('100000.00'))
    resultado = validar_techo(poa)
    assert resultado['techo'] == '0.00'
    assert resultado['excede'] is True
    assert 'dentro del techo' not in resultado['mensaje']
    assert 'techo presupuestario configurado' in resultado['mensaje']


def test_validar_techo_sin_techo_formulado_cero(poa_2027):
    """C3: techo 0 + formulado 0 → no excede ('Sin techo presupuestario
    configurado'), nunca 'excede'."""
    poa, _ = poa_2027
    resultado = validar_techo(poa)
    assert resultado['techo'] == '0.00'
    assert resultado['formulado'] == '0.00'
    assert resultado['excede'] is False
    assert 'dentro del techo' not in resultado['mensaje']
