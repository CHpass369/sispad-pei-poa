"""
Pins de los fixes confirmados en la 4R (slice S2, PR #2).

Cubren, sobre un techo con JERARQUÍA sintética (estado post-0004):

- K1: TechoPresupuestario.monto_distribuido cuenta SOLO hojas activas
  (delega en budget_service.get_distributed) — no 2× el árbol.
- K2: get_reserved en el techo suma SOLO hojas activas (40→20) y
  saldo_disponible == resumen del motor.
- W-real reactivación: al reactivar una hoja inactiva NO se resta su
  monto viejo de Σ(hijos) (solo se resta si la fila estaba activa).
- W8: resumen_techos(qs) batch == get_techo_resumen(techo) por techo
  (mismo contrato de salida, sin N+1).
"""
from datetime import date
from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError

from apps.accounts.models import Usuario
from apps.catalogos.models import FuenteFinanciamiento, OrganismoFinanciador
from apps.gestion.models import GestionFiscal
from apps.techos.models import DistribucionTecho, TechoPresupuestario
from apps.techos.services import budget_service

NOMBRE_CATEGORIA_SINTETICA = 'MIGRACION LEGACY 0004'


@pytest.fixture
def techo_jerarquico(db):
    """Techo 1:1 con jerarquía sintética post-0004: categoría 450/20 +
    hoja 300/10 + hoja 150/10 (el árbol completo sumaría 900/40 si se
    contara 2×; las hojas suman 450/20)."""
    usuario = Usuario.objects.create_user(
        email='fixes_4r@gamsacaba.gob.bo', password='test123',
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
    gestion = GestionFiscal.objects.create(anio=2026, estado='preparacion')
    techo = TechoPresupuestario.objects.create(
        gestion=2026, gestion_fiscal=gestion, monto_total=Decimal('1000.00'),
        fuente=fuente, organismo=organismo,
    )
    categoria = DistribucionTecho.objects.create(
        techo=techo, concepto=NOMBRE_CATEGORIA_SINTETICA,
        monto_asignado=Decimal('450.00'), monto_reserva=Decimal('20.00'),
        activo=True, version=1,
    )
    DistribucionTecho.objects.create(
        techo=techo, padre=categoria, monto_asignado=Decimal('300.00'),
        monto_reserva=Decimal('10.00'), activo=True, version=1,
    )
    hoja2 = DistribucionTecho.objects.create(
        techo=techo, padre=categoria, monto_asignado=Decimal('150.00'),
        monto_reserva=Decimal('10.00'), activo=True, version=1,
    )
    return {
        'usuario': usuario, 'techo': techo, 'categoria': categoria,
        'hoja1': DistribucionTecho.objects.get(
            techo=techo, padre=categoria, monto_asignado=Decimal('300.00'),
        ),
        'hoja2': hoja2,
    }


# ---------------------------------------------------------------------------
# K1 — monto_distribuido cuenta solo hojas activas (no 2× la jerarquía)
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_k1_monto_distribuido_suma_solo_hojas(techo_jerarquico):
    """monto_distribuido == Σ hojas (450), no 900 (árbol completo)."""
    techo = techo_jerarquico['techo']
    assert techo.monto_distribuido == Decimal('450.00')
    assert techo.monto_distribuido == budget_service.get_distributed(techo)
    # Triangulación: el property NO es el árbol completo.
    assert techo.monto_distribuido != Decimal('900.00')


@pytest.mark.django_db
def test_k1_monto_distribuido_igual_motor(techo_jerarquico):
    """monto_distribuido (property) == monto_distribuido del resumen del motor."""
    techo = techo_jerarquico['techo']
    resumen = budget_service.get_techo_resumen(techo)
    assert techo.monto_distribuido == resumen['monto_distribuido'] == Decimal('450.00')


# ---------------------------------------------------------------------------
# K2 — get_reserved solo hojas activas y saldo consistente con el resumen
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_k2_get_reserved_suma_solo_hojas(techo_jerarquico):
    """get_reserved(techo) == Σ reservas de hojas (20), no 40 (árbol)."""
    techo = techo_jerarquico['techo']
    assert budget_service.get_reserved(techo) == Decimal('20.00')
    assert budget_service.get_reserved(techo) != Decimal('40.00')


@pytest.mark.django_db
def test_k2_saldo_disponible_igual_resumen(techo_jerarquico):
    """saldo_disponible == resumen.saldo_disponible (misma ecuación D11)."""
    techo = techo_jerarquico['techo']
    resumen = budget_service.get_techo_resumen(techo)
    esperado = Decimal('1000.00') - Decimal('450.00') - Decimal('20.00')
    assert techo.saldo_disponible == esperado == Decimal('530.00')
    assert techo.saldo_disponible == resumen['saldo_disponible']


# ---------------------------------------------------------------------------
# W-real reactivación — solo se resta el monto viejo si la fila estaba activa
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_wreal_reactivar_hoja_no_resta_monto_inactivo(techo_jerarquico):
    """Reactivar una hoja inactiva NO resta su monto viejo de Σ(hijos):
    con los hermanos al tope, la reactivación que excede al padre es
    rechazada (antes el bug la dejaba pasar)."""
    categoria = techo_jerarquico['categoria']
    hoja2 = techo_jerarquico['hoja2']

    # Desactivar la hoja 2 (150): queda fuera de Σ(hijos) y de Σ hojas.
    hoja2.activo = False
    hoja2.save()

    # Reactivarla con 200: Σ(hijos activos) = 300 (hoja1) + 200 = 500 > 450.
    hoja2.monto_asignado = Decimal('200.00')
    hoja2.activo = True
    with pytest.raises(ValidationError):
        hoja2.save()

    # Triangulación: reactivar dentro del margen (150) sigue siendo válido.
    hoja2.monto_asignado = Decimal('150.00')
    hoja2.save()
    assert DistribucionTecho.objects.filter(padre=categoria, activo=True).count() == 2


@pytest.mark.django_db
def test_wreal_editar_hoja_activa_sigue_resta_monto_viejo(techo_jerarquico):
    """Regresión del fix: editar una hoja ACTIVA sigue restando su monto
    viejo de Σ(hijos) (300→320: 150 + 320 > 450 → rechazado; sin el
    descuento del monto viejo activo ninguna edición bajaría de tope)."""
    hoja1 = techo_jerarquico['hoja1']
    # 300 → 320: Σ(hijos) tras el descuento = 150 (hoja2) + 320 = 470 > 450.
    hoja1.monto_asignado = Decimal('320.00')
    with pytest.raises(ValidationError):
        hoja1.save()
    # 300 → 250: 150 + 250 = 400 ≤ 450 → válido (el descuento del monto
    # viejo activo es lo que permite bajar el peso de la fila).
    hoja1.monto_asignado = Decimal('250.00')
    hoja1.save()
    assert hoja1.monto_asignado == Decimal('250.00')


# ---------------------------------------------------------------------------
# W8 — resumen_techos(qs) batch == get_techo_resumen(techo)
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_w8_resumen_techos_batch_igual_por_techo(techo_jerarquico):
    """resumen_techos(qs) produce el MISMO dict que get_techo_resumen."""
    techo = techo_jerarquico['techo']
    batch = budget_service.resumen_techos([techo])
    assert str(techo.id) in batch
    assert batch[str(techo.id)] == budget_service.get_techo_resumen(techo)


@pytest.mark.django_db
def test_w8_resumen_techos_conjunto(techo_jerarquico):
    """resumen_techos con varios techos: un dict por techo, sin mezclar."""
    techo = techo_jerarquico['techo']
    vig = date(2026, 1, 1)
    fuente = techo.fuente
    gestion = GestionFiscal.objects.create(anio=2027, estado='preparacion')
    otro = TechoPresupuestario.objects.create(
        gestion=2027, gestion_fiscal=gestion, monto_total=Decimal('500.00'),
        fuente=fuente,
    )
    batch = budget_service.resumen_techos([techo, otro])
    assert set(batch) == {str(techo.id), str(otro.id)}
    assert batch[str(otro.id)]['monto_distribuido'] == Decimal('0.00')
    assert batch[str(otro.id)]['saldo_disponible'] == Decimal('500.00')
