"""
Tests de ecuación pin del núcleo presupuestario (slice S1).

Fijan el comportamiento actual de las 6 implementaciones de saldo ANTES del
refactor de delegación al BudgetAllocationService (design D11) y verifican,
después del refactor, que las ecuaciones dan resultados idénticos (no cambia
ningún saldo).

Ecuación 2027: recursos 245.290.497,00 - gastos obligatorios 6.464.396,00
= distribuible 238.826.101,00.
"""
import io as _io
import types
from datetime import date
from decimal import Decimal

import pytest
from django.utils import timezone

from apps.accounts.models import Usuario
from apps.catalogos.models import FuenteFinanciamiento
from apps.presupuesto.models import ProgramaPresupuestario
from apps.sis_poa.models import (
    AccionCortoPlazo,
    Actividad,
    Operacion,
    PoAInstitucional,
    ProgramacionActividad,
)
from apps.sis_poa.migration_v2 import validar_techo
from apps.techos.models import (
    DistribucionTecho,
    GastoObligatorio,
    MovimientoTecho,
    RecursoTecho,
    TechoPresupuestario,
)
from apps.techos.services import obtener_saldo_disponible, resumen_techo
from apps.workflow.consolidacion import (
    _total_distribuido,
    _total_techo,
    consolidar_poa_institucional,
)

MONTO_RECURSOS = Decimal('245290497.00')
MONTO_GASTOS = Decimal('6464396.00')
MONTO_DISTRIBUIBLE = Decimal('238826101.00')
MONTO_DISTRIBUIDO = Decimal('50000000.00')
SALDO_ESPERADO = MONTO_DISTRIBUIBLE - MONTO_DISTRIBUIDO  # 188.826.101,00


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
def usuario(db):
    return Usuario.objects.create_user(
        email='ecuaciones_test@gamsacaba.gob.bo', password='test123',
    )


# ---------------------------------------------------------------------------
# 1. TechoPresupuestario.saldo_disponible (property)
# ---------------------------------------------------------------------------

def test_saldo_disponible_property_ecuacion_2027(techo_2027):
    """saldo_disponible = techo - gastos obligatorios - distribuido."""
    assert techo_2027.monto_total - MONTO_GASTOS == MONTO_DISTRIBUIBLE
    assert techo_2027.saldo_disponible == SALDO_ESPERADO


def test_saldo_disponible_property_sin_distribuir(techo_2027):
    """Ecuación 2027 con distribución cero: el saldo es el distribuible."""
    techo = TechoPresupuestario.objects.create(
        gestion=2027, monto_total=MONTO_RECURSOS, fuente=techo_2027.fuente,
        concepto='Techo 2027 sin distribuir',
    )
    RecursoTecho.objects.create(
        techo=techo, fuente=techo_2027.fuente,
        concepto='Coparticipación Tributaria', monto=MONTO_RECURSOS,
    )
    GastoObligatorio.objects.create(
        techo=techo, fuente=techo_2027.fuente,
        denominacion='Renta Dignidad', monto=MONTO_GASTOS,
    )
    assert techo.saldo_disponible == MONTO_DISTRIBUIBLE


# ---------------------------------------------------------------------------
# 2. services.obtener_saldo_disponible (semántica legacy por movimientos)
# ---------------------------------------------------------------------------

def test_obtener_saldo_disponible_sin_movimientos(techo_2027):
    """Sin movimientos aprobados el saldo legacy es el monto_total."""
    assert obtener_saldo_disponible(techo_2027) == MONTO_RECURSOS


def test_obtener_saldo_disponible_con_reduccion_aprobada(techo_2027, usuario):
    """Una reducción aprobada descuenta del saldo legacy."""
    MovimientoTecho.objects.create(
        techo=techo_2027, movement_type='reduccion',
        amount=Decimal('500000.00'), justification='Reducción pin',
        requested_by=usuario, approved_by=usuario, date=timezone.now(),
    )
    assert obtener_saldo_disponible(techo_2027) == MONTO_RECURSOS - Decimal('500000.00')


# ---------------------------------------------------------------------------
# 3. services.resumen_techo
# ---------------------------------------------------------------------------

def test_resumen_techo_claves_y_valores(techo_2027):
    resumen = resumen_techo(techo_2027)
    assert resumen['techo_id'] == str(techo_2027.id)
    assert resumen['gestion'] == 2027
    assert resumen['monto_total'] == MONTO_RECURSOS
    assert resumen['total_recursos'] == MONTO_RECURSOS
    assert resumen['total_gastos_obligatorios'] == MONTO_GASTOS
    assert resumen['monto_distribuido'] == MONTO_DISTRIBUIDO
    assert resumen['saldo_disponible'] == SALDO_ESPERADO
    assert resumen['excede'] is False


# ---------------------------------------------------------------------------
# 4. workflow/consolidacion: _total_techo / _total_distribuido / saldo_por_distribuir
# ---------------------------------------------------------------------------

def test_workflow_total_techo_por_gestion(techo_2027):
    assert _total_techo(2027) == MONTO_RECURSOS


def test_workflow_total_distribuido_por_gestion(techo_2027):
    assert _total_distribuido(2027) == MONTO_DISTRIBUIDO


def test_workflow_saldo_por_distribuir(techo_2027):
    totales = consolidar_poa_institucional(2027)['totales']
    assert totales['techo'] == MONTO_RECURSOS
    assert totales['techo_distribuido'] == MONTO_DISTRIBUIDO
    assert totales['saldo_por_distribuir'] == MONTO_RECURSOS - MONTO_DISTRIBUIDO


# ---------------------------------------------------------------------------
# 5. reportes/services.py: techo por programa en el consolidado
# ---------------------------------------------------------------------------

def test_reportes_consolidado_techo_por_programa(monkeypatch, techo_2027):
    """El consolidado muestra el techo asignado por programa (sin float)."""
    import openpyxl

    import apps.reportes.services as reportes_mod

    prog = ProgramaPresupuestario.objects.create(
        codigo='001', nombre='Programa 1', gestion=2027,
    )
    DistribucionTecho.objects.create(
        techo=techo_2027, programa=prog, monto_asignado=Decimal('30000000.00'),
    )

    captured = _io.BytesIO()
    monkeypatch.setattr(
        reportes_mod, 'io', types.SimpleNamespace(BytesIO=lambda: captured),
    )
    reportes_mod.generar_poa_consolidado_xlsx(2027)

    ws = openpyxl.load_workbook(captured).active
    fila = 4  # primera fila de datos (encabezados en fila 3)
    assert ws.cell(row=fila, column=4).value == 30000000  # Techo (Bs)
    assert ws.cell(row=fila, column=5).value == 30000000  # Saldo (Bs)
    assert ws.cell(row=fila, column=7).value == 'Completo'


# ---------------------------------------------------------------------------
# 6. sis_poa/migration_v2.validar_techo
# ---------------------------------------------------------------------------

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


def test_validar_techo_dentro_del_techo(techo_2027, poa_2027):
    poa, actividad = poa_2027
    _programar_financiero(actividad, Decimal('100000.00'))
    resultado = validar_techo(poa)
    assert resultado['excede'] is False
    assert resultado['techo'] == '245290497.00'
    assert resultado['formulado'] == '100000.0000'


def test_validar_techo_excede(techo_2027, poa_2027):
    poa, actividad = poa_2027
    _programar_financiero(actividad, Decimal('300000000.00'))
    resultado = validar_techo(poa)
    assert resultado['excede'] is True
    assert resultado['techo'] == '245290497.00'


# ---------------------------------------------------------------------------
# 7. BudgetAllocationService (motor único): las ecuaciones también vía servicio
# ---------------------------------------------------------------------------

from apps.techos.services import BudgetAllocationService, budget_service  # noqa: E402


def test_service_ecuacion_2027_resumen(techo_2027):
    """get_techo_resumen reproduce el resumen legacy y suma claves nuevas."""
    resumen = budget_service.get_techo_resumen(techo_2027)
    assert resumen['techo_id'] == str(techo_2027.id)
    assert resumen['gestion'] == 2027
    assert resumen['monto_total'] == MONTO_RECURSOS
    assert resumen['total_recursos'] == MONTO_RECURSOS
    assert resumen['total_gastos_obligatorios'] == MONTO_GASTOS
    assert resumen['monto_distribuido'] == MONTO_DISTRIBUIDO
    assert resumen['saldo_disponible'] == SALDO_ESPERADO
    assert resumen['excede'] is False
    assert resumen['techo_distribuible'] == MONTO_DISTRIBUIBLE
    assert resumen['monto_reservado'] == Decimal('0.00')


def test_service_get_available_ecuacion_2027(techo_2027):
    assert budget_service.get_available(techo_2027) == SALDO_ESPERADO


def test_service_totales_techo(techo_2027):
    assert budget_service.get_total_recursos(techo_2027) == MONTO_RECURSOS
    assert budget_service.get_total_gastos_obligatorios(techo_2027) == MONTO_GASTOS
    assert budget_service.get_techo_distribuible(techo_2027) == MONTO_DISTRIBUIBLE


def test_service_get_distributed_nodo_hoja(techo_2027):
    dist = techo_2027.distribuciones.get()
    assert budget_service.get_distributed_nodo(dist) == MONTO_DISTRIBUIDO


def test_service_agregados_por_gestion(techo_2027):
    assert budget_service.get_techo_agregado_gestion(2027) == MONTO_RECURSOS
    assert budget_service.get_distribuido_agregado_gestion(2027) == MONTO_DISTRIBUIDO
    assert budget_service.get_saldo_por_distribuir_gestion(2027) == (
        MONTO_RECURSOS - MONTO_DISTRIBUIDO
    )


def test_service_get_distribuido_por_programa(techo_2027):
    prog = ProgramaPresupuestario.objects.create(
        codigo='002', nombre='Programa 2', gestion=2027,
    )
    DistribucionTecho.objects.create(
        techo=techo_2027, programa=prog, monto_asignado=Decimal('30000000.00'),
    )
    assert budget_service.get_distribuido_por_programa(prog) == Decimal('30000000.00')


def test_service_estado_techo_parcial(techo_2027):
    assert budget_service.estado_techo(techo_2027) == 'DISTRIBUCION_PARCIAL'


def test_service_estado_techo_sin_configurar(techo_2027):
    techo = TechoPresupuestario.objects.create(
        gestion=2027, monto_total=MONTO_RECURSOS, fuente=techo_2027.fuente,
        concepto='Sin distribución',
    )
    assert budget_service.estado_techo(techo) == 'SIN_CONFIGURAR'


def test_service_estado_techo_inconsistente(techo_2027):
    """Σ distribuido > distribuible => INCONSISTENTE (fail-loud, C3)."""
    DistribucionTecho.objects.bulk_create([
        DistribucionTecho(
            techo=techo_2027, monto_asignado=MONTO_DISTRIBUIBLE + Decimal('1.00'),
        ),
    ])
    assert budget_service.estado_techo(techo_2027) == 'INCONSISTENTE'


def test_service_validate_allocation_dentro(techo_2027):
    resultado = budget_service.validate_allocation(techo_2027, Decimal('10000000.00'))
    assert resultado['valido'] is True
    assert resultado['excede'] is False
    assert resultado['monto_solicitado'] == Decimal('10000000.00')
    assert resultado['saldo_disponible'] == SALDO_ESPERADO


def test_service_validate_allocation_excede(techo_2027):
    resultado = budget_service.validate_allocation(techo_2027, Decimal('200000000.00'))
    assert resultado['valido'] is False
    assert resultado['excede'] is True
    assert resultado['saldo_disponible'] == SALDO_ESPERADO


def test_service_validate_allocation_respeto_reserva(techo_2027):
    """La guardia a nivel techo resta reservas (C3): la capacidad efectiva
    es min(saldo_bolsa, techo_distribuible - Σ hojas - reservado_total)."""
    DistribucionTecho.objects.create(
        techo=techo_2027, monto_asignado=Decimal('0.00'),
        monto_reserva=Decimal('10000000.00'),
    )
    resultado = budget_service.validate_allocation(techo_2027, Decimal('180000000.00'))
    assert resultado['valido'] is False
    assert resultado['excede'] is True
    assert resultado['saldo_disponible'] == SALDO_ESPERADO - Decimal('10000000.00')
    assert budget_service.validate_allocation(
        techo_2027, Decimal('178826101.00'),
    )['valido'] is True


def test_service_validate_allocation_monto_negativo(techo_2027):
    resultado = budget_service.validate_allocation(techo_2027, Decimal('-1.00'))
    assert resultado['valido'] is False
    assert 'negativo' in resultado['mensaje']


def test_service_can_allocate(techo_2027):
    assert budget_service.can_allocate(techo_2027, SALDO_ESPERADO) is True
    assert budget_service.can_allocate(
        techo_2027, SALDO_ESPERADO + Decimal('0.01'),
    ) is False


def test_service_get_saldo_por_movimientos(techo_2027, usuario):
    """Compatibilidad legacy V1: saldo por movimientos aprobados."""
    MovimientoTecho.objects.create(
        techo=techo_2027, movement_type='reduccion',
        amount=Decimal('500000.00'), justification='Reducción pin',
        requested_by=usuario, approved_by=usuario, date=timezone.now(),
    )
    assert budget_service.get_saldo_por_movimientos(techo_2027) == (
        MONTO_RECURSOS - Decimal('500000.00')
    )
