"""
Tests de los modelos del núcleo de techos (slice S2, jerárquico).

Cubren:
- Uniques con nulls_distinct=False (C4): TechoRecursoGrupo y
  BolsaPresupuestaria rechazan duplicados con organismo NULL.
- Ledger inmutable (C7): MovimientoPresupuestario solo admite creación;
  save() posterior y delete() lanzan DomainError.
- Estados operativos de gestión (Q3): VIGENTE/ANULADA derivados por el
  motor y estados calculados de techo (DD3).
- Coherencia techo ↔ gestión en clean() (R2.1).
- Conciliación de grupos FF/OF (Q2): PENDIENTE/CONCILIADO/CON_DIFERENCIA
  sin umbral de silencio y sin_clasificar calculado.
"""
from datetime import date
from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from apps.accounts.models import Usuario
from apps.catalogos.models import FuenteFinanciamiento, OrganismoFinanciador
from apps.core.exceptions import DomainError
from apps.gestion.models import GestionFiscal
from apps.techos.models import (
    BolsaPresupuestaria,
    DistribucionTecho,
    MovimientoPresupuestario,
    TechoPresupuestario,
    TechoRecursoDetalle,
    TechoRecursoGrupo,
)
from apps.techos.services import budget_service


@pytest.fixture
def base():
    """Escenario base: usuario, fuente, organismo, gestión y techo 1:1."""
    user = Usuario.objects.create_user(
        email='nucleo_s2@gamsacaba.gob.bo', password='test123',
        first_name='Nucleo', last_name='S2',
    )
    vig = date(2026, 1, 1)
    fuente = FuenteFinanciamiento.objects.create(
        codigo='41-113', gestion=2026,
        denominacion='Coparticipación Tributaria', fecha_vigencia_desde=vig,
    )
    organismo = OrganismoFinanciador.objects.create(
        codigo='GOB-MUN', gestion=2026,
        denominacion='Gobierno Municipal', fecha_vigencia_desde=vig,
    )
    gestion = GestionFiscal.objects.create(anio=2026, estado='vigente')
    techo = TechoPresupuestario.objects.create(
        gestion=2026, gestion_fiscal=gestion, monto_total=Decimal('1000.00'),
        fuente=fuente, organismo=organismo,
    )
    return {
        'user': user, 'fuente': fuente, 'organismo': organismo,
        'gestion': gestion, 'techo': techo,
    }


# ---------------------------------------------------------------------------
# Uniques con nulls_distinct=False (C4)
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_unique_grupo_organismo_nulo(base):
    """Dos grupos con el mismo (techo, fuente) y organismo NULL colisionan."""
    TechoRecursoGrupo.objects.create(
        techo=base['techo'], fuente=base['fuente'], organismo=None,
        monto=Decimal('100.00'),
    )
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            TechoRecursoGrupo.objects.create(
                techo=base['techo'], fuente=base['fuente'], organismo=None,
                monto=Decimal('50.00'),
            )


@pytest.mark.django_db
def test_unique_grupo_organismo_distinto_no_colisiona(base):
    """Organismos distintos (o null vs set) no colisionan (triangulación)."""
    otro_org = OrganismoFinanciador.objects.create(
        codigo='GOB-DEP', gestion=2026,
        denominacion='Gobierno Departamental',
        fecha_vigencia_desde=date(2026, 1, 1),
    )
    TechoRecursoGrupo.objects.create(
        techo=base['techo'], fuente=base['fuente'], organismo=None,
        monto=Decimal('100.00'),
    )
    TechoRecursoGrupo.objects.create(
        techo=base['techo'], fuente=base['fuente'], organismo=otro_org,
        monto=Decimal('50.00'),
    )
    assert TechoRecursoGrupo.objects.filter(techo=base['techo']).count() == 2


@pytest.mark.django_db
def test_unique_bolsa_organismo_nulo(base):
    """Dos bolsas con el mismo (techo, fuente, organismo NULL, tipo) colisionan."""
    BolsaPresupuestaria.objects.create(
        techo=base['techo'], fuente=base['fuente'], organismo=None,
        tipo_gasto=BolsaPresupuestaria.TipoGasto.CORRIENTE,
        monto_inicial=Decimal('100.00'), monto_ajustes=Decimal('0.00'),
        monto_vigente=Decimal('100.00'),
    )
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            BolsaPresupuestaria.objects.create(
                techo=base['techo'], fuente=base['fuente'], organismo=None,
                tipo_gasto=BolsaPresupuestaria.TipoGasto.CORRIENTE,
                monto_inicial=Decimal('50.00'), monto_ajustes=Decimal('0.00'),
                monto_vigente=Decimal('50.00'),
            )


@pytest.mark.django_db
def test_unique_bolsa_tipo_distinto_no_colisiona(base):
    """CORRIENTE vs INVERSION no colisionan (triangulación)."""
    BolsaPresupuestaria.objects.create(
        techo=base['techo'], fuente=base['fuente'], organismo=None,
        tipo_gasto=BolsaPresupuestaria.TipoGasto.CORRIENTE,
        monto_inicial=Decimal('100.00'), monto_ajustes=Decimal('0.00'),
        monto_vigente=Decimal('100.00'),
    )
    BolsaPresupuestaria.objects.create(
        techo=base['techo'], fuente=base['fuente'], organismo=None,
        tipo_gasto=BolsaPresupuestaria.TipoGasto.INVERSION,
        monto_inicial=Decimal('50.00'), monto_ajustes=Decimal('0.00'),
        monto_vigente=Decimal('50.00'),
    )
    assert BolsaPresupuestaria.objects.filter(techo=base['techo']).count() == 2


# ---------------------------------------------------------------------------
# Ledger inmutable (C7)
# ---------------------------------------------------------------------------

def _crear_movimiento(base):
    return MovimientoPresupuestario.objects.create(
        techo=base['techo'],
        tipo=MovimientoPresupuestario.TipoMovimiento.DISTRIBUCION,
        monto=Decimal('100.00'),
        saldo_antes=Decimal('500.00'), saldo_despues=Decimal('400.00'),
        usuario=base['user'], justificacion='Distribución inicial',
        fecha=date(2026, 3, 1),
    )


@pytest.mark.django_db
def test_ledger_creacion_valida(base):
    """La creación del ledger es válida (save() en _state.adding)."""
    movimiento = _crear_movimiento(base)
    assert movimiento.pk is not None
    assert movimiento.checksum == ''  # el checksum encadenado es S3
    assert MovimientoPresupuestario.objects.count() == 1


@pytest.mark.django_db
def test_ledger_no_admite_segunda_escritura(base):
    """save() sobre un movimiento persistido lanza DomainError (C7)."""
    movimiento = _crear_movimiento(base)
    with pytest.raises(DomainError):
        movimiento.save()


@pytest.mark.django_db
def test_ledger_no_admite_delete(base):
    """delete() lanza DomainError (C7): el ledger es inmutable."""
    movimiento = _crear_movimiento(base)
    with pytest.raises(DomainError):
        movimiento.delete()
    assert MovimientoPresupuestario.objects.count() == 1


@pytest.mark.django_db
def test_ledger_bolsa_nula_permitida(base):
    """Movimientos a nivel techo con bolsa null son válidos (INCREMENTO)."""
    MovimientoPresupuestario.objects.create(
        techo=base['techo'], bolsa=None,
        tipo=MovimientoPresupuestario.TipoMovimiento.INCREMENTO,
        monto=Decimal('50.00'),
        saldo_antes=Decimal('500.00'), saldo_despues=Decimal('550.00'),
        usuario=base['user'], justificacion='Incremento a nivel techo',
        fecha=date(2026, 3, 2),
    )
    assert MovimientoPresupuestario.objects.count() == 1


# ---------------------------------------------------------------------------
# Estados operativos de gestión (Q3) y estados de techo (DD3)
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_estado_techo_vigente_con_gestion_vigente(base):
    """Gestión 'vigente' → estado de techo VIGENTE."""
    assert budget_service.estado_techo(base['techo']) == 'VIGENTE'


@pytest.mark.django_db
def test_estado_techo_cerrado_con_gestion_anulada(base):
    """Gestión 'anulada' → estado de techo CERRADO."""
    base['gestion'].estado = GestionFiscal.Estado.ANULADA
    base['gestion'].save()
    assert budget_service.estado_techo(base['techo']) == 'CERRADO'


@pytest.mark.django_db
def test_estado_bolsa_disponible(base):
    """Bolsa sin distribuir → DISPONIBLE (estado calculado DD3)."""
    bolsa = BolsaPresupuestaria.objects.create(
        techo=base['techo'], fuente=base['fuente'], organismo=base['organismo'],
        tipo_gasto=BolsaPresupuestaria.TipoGasto.CORRIENTE,
        monto_inicial=Decimal('100.00'), monto_ajustes=Decimal('0.00'),
        monto_vigente=Decimal('100.00'),
    )
    assert budget_service.estado_bolsa(bolsa) == 'DISPONIBLE'


# ---------------------------------------------------------------------------
# Coherencia techo ↔ gestión en clean() (R2.1)
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_clean_techo_gestion_coherente(base):
    """clean() acepta gestion == gestion_fiscal.anio (R2.1)."""
    gestion = GestionFiscal.objects.create(anio=2027, estado='preparacion')
    techo = TechoPresupuestario(
        gestion=2027, gestion_fiscal=gestion,
        monto_total=Decimal('100.00'), fuente=base['fuente'],
    )
    techo.full_clean()  # no debe lanzar


@pytest.mark.django_db
def test_clean_techo_gestion_incoherente_rechazado(base):
    """clean() rechaza gestion != gestion_fiscal.anio (R1.3)."""
    gestion = GestionFiscal.objects.create(anio=2027, estado='preparacion')
    techo = TechoPresupuestario(
        gestion=2028, gestion_fiscal=gestion,
        monto_total=Decimal('100.00'), fuente=base['fuente'],
    )
    with pytest.raises(ValidationError):
        techo.full_clean()


# ---------------------------------------------------------------------------
# Conciliación de grupos FF/OF (Q2) — sin umbral de silencio
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_conciliacion_grupo_pendiente_sin_detalles(base):
    """Grupo sin detalles → PENDIENTE (Q2)."""
    grupo = TechoRecursoGrupo.objects.create(
        techo=base['techo'], fuente=base['fuente'], organismo=base['organismo'],
        monto=Decimal('100.00'),
    )
    assert budget_service.get_estado_conciliacion(grupo) == 'PENDIENTE'


@pytest.mark.django_db
def test_conciliacion_grupo_conciliado(base):
    """Σ detalles == monto → CONCILIADO con diferencia 0 (R2.5)."""
    grupo = TechoRecursoGrupo.objects.create(
        techo=base['techo'], fuente=base['fuente'], organismo=base['organismo'],
        monto=Decimal('100.00'),
    )
    TechoRecursoDetalle.objects.create(
        grupo=grupo, rubro='1', concepto='Detalle A', monto=Decimal('60.00'),
    )
    TechoRecursoDetalle.objects.create(
        grupo=grupo, rubro='2', concepto='Detalle B', monto=Decimal('40.00'),
    )
    assert budget_service.get_estado_conciliacion(grupo) == 'CONCILIADO'
    assert budget_service.get_diferencia(grupo) == Decimal('0.00')


@pytest.mark.django_db
def test_conciliacion_grupo_con_diferencia_visible(base):
    """|Σ detalles − monto| > 0 → CON_DIFERENCIA visible (Q2, 0,02)."""
    grupo = TechoRecursoGrupo.objects.create(
        techo=base['techo'], fuente=base['fuente'], organismo=base['organismo'],
        monto=Decimal('181658084.00'),
    )
    TechoRecursoDetalle.objects.create(
        grupo=grupo, rubro='1', concepto='Coparticipación',
        monto=Decimal('181658084.02'),
    )
    assert budget_service.get_estado_conciliacion(grupo) == 'CON_DIFERENCIA'
    assert budget_service.get_diferencia(grupo) == Decimal('0.02')


@pytest.mark.django_db
def test_sin_clasificar_grupo(base):
    """sin_clasificar = monto − corriente − inversion (R4.4)."""
    grupo = TechoRecursoGrupo.objects.create(
        techo=base['techo'], fuente=base['fuente'], organismo=base['organismo'],
        monto=Decimal('100.00'), monto_corriente=Decimal('20.00'),
        monto_inversion=Decimal('60.00'),
    )
    assert budget_service.get_sin_clasificar(grupo) == Decimal('20.00')


# ---------------------------------------------------------------------------
# Jerarquía: SUM(hijos) ≤ padre en clean() (R4.2)
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_clean_distribucion_hijos_no_exceden_padre(base):
    """Hoja cuyo monto excede al padre → ValidationError (R4.2)."""
    categoria = DistribucionTecho.objects.create(
        techo=base['techo'], monto_asignado=Decimal('100.00'),
        monto_reserva=Decimal('0.00'), activo=True, version=1,
    )
    hoja = DistribucionTecho(
        techo=base['techo'], padre=categoria, unidad=None,
        monto_asignado=Decimal('120.00'), monto_reserva=Decimal('0.00'),
        activo=True, version=1,
    )
    with pytest.raises(ValidationError):
        hoja.full_clean()


@pytest.mark.django_db
def test_clean_distribucion_hijos_ok_dentro_del_padre(base):
    """Hoja dentro del monto del padre → válida (triangulación)."""
    categoria = DistribucionTecho.objects.create(
        techo=base['techo'], monto_asignado=Decimal('100.00'),
        monto_reserva=Decimal('0.00'), activo=True, version=1,
    )
    hoja = DistribucionTecho(
        techo=base['techo'], padre=categoria, unidad=None,
        monto_asignado=Decimal('60.00'), monto_reserva=Decimal('0.00'),
        activo=True, version=1,
    )
    hoja.full_clean()
    hoja.save()
    assert DistribucionTecho.objects.filter(padre=categoria).count() == 1
