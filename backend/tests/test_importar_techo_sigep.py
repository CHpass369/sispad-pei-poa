"""Tests del management command importar_techo_sigep (GAM Sacaba, gestión 2027)."""
from decimal import Decimal

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from apps.accounts.models import Usuario
from apps.budget.models import (
    CeilingResource,
    DirectiveCeiling,
    DirectiveCeilingVersion,
    MandatoryExpense,
)
from apps.budget.services import (
    aprobar,
    composicion_techo,
    enviar_a_revision,
    fijar_techo,
    gestion_habilitada,
    habilitar_gestion,
)
from apps.catalogos.models import RubroRecurso
from apps.gestion.models import GestionFiscal


def _cargar_catalogos():
    call_command('importar_catalogos_sacaba', gestion=2027)


def _habilitar_gestion_2027():
    gestion = GestionFiscal.objects.get(anio=2027)
    if not gestion_habilitada(gestion):
        habilitar_gestion(gestion, None)
    gestion.refresh_from_db()
    return gestion


def test_carga_techo_sigep_completo(db):
    _cargar_catalogos()
    gestion = _habilitar_gestion_2027()

    call_command('importar_techo_sigep', gestion=2027)

    ceiling = DirectiveCeiling.objects.get(gestion=gestion)
    assert ceiling.estado == 'BORRADOR'
    assert ceiling.version_actual == 1

    version = ceiling.versiones.get(numero=1)
    assert version.estado == 'BORRADOR'
    assert version.inmutable is False
    assert not version.hash

    assert RubroRecurso.objects.filter(
        codigo__in=['19211', '19212'], gestion__anio=2027
    ).count() == 2

    recursos = list(CeilingResource.objects.filter(version=version))
    assert len(recursos) == 5
    assert all(r.origen == 'SIGEP' for r in recursos)
    total_recursos = sum((r.monto for r in recursos), Decimal('0.00'))
    assert total_recursos == Decimal('245290497.00')

    obligatorios = list(MandatoryExpense.objects.filter(version=version))
    assert len(obligatorios) == 3
    total_obligatorios = sum((g.monto for g in obligatorios), Decimal('0.00'))
    assert total_obligatorios == Decimal('6464396.00')

    comp = composicion_techo(ceiling)
    assert comp['sigep'] == Decimal('245290497.00')
    assert comp['techo_bruto'] == Decimal('245290497.00')
    assert comp['techo_distribuible'] == (
        Decimal('245290497.00') - Decimal('6464396.00')
    )


def test_idempotente(db):
    _cargar_catalogos()
    _habilitar_gestion_2027()

    call_command('importar_techo_sigep', gestion=2027)
    call_command('importar_techo_sigep', gestion=2027)

    assert DirectiveCeiling.objects.count() == 1
    assert DirectiveCeilingVersion.objects.count() == 1
    ceiling = DirectiveCeiling.objects.get(gestion__anio=2027)
    version = ceiling.versiones.get(numero=1)
    assert version.recursos.count() == 5
    assert version.gastos_obligatorios.count() == 3
    assert RubroRecurso.objects.filter(gestion__anio=2027).count() == 2


def test_gestion_no_habilitada_se_habilita(db):
    _cargar_catalogos()
    gestion = GestionFiscal.objects.get(anio=2027)
    gestion.estado = GestionFiscal.Estado.CONFIGURACION
    gestion.save(update_fields=['estado'])

    call_command('importar_techo_sigep', gestion=2027)

    gestion.refresh_from_db()
    assert gestion.estado == GestionFiscal.Estado.HABILITADA
    assert gestion.fecha_apertura is not None
    assert DirectiveCeiling.objects.filter(gestion=gestion).exists()


def test_no_edita_techo_fijado(db):
    _cargar_catalogos()
    _habilitar_gestion_2027()
    call_command('importar_techo_sigep', gestion=2027)

    ceiling = DirectiveCeiling.objects.get(gestion__anio=2027)
    version = ceiling.versiones.get(numero=1)
    admin = Usuario.objects.create_superuser(
        email='admin@techo.test', password='test2026'
    )
    enviar_a_revision(version, admin)
    aprobar(version, admin)
    fijar_techo(version, admin)

    with pytest.raises(CommandError) as exc:
        call_command('importar_techo_sigep', gestion=2027)
    assert 'FIJADA' in str(exc.value)
