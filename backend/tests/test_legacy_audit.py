"""Contratos de la herramienta de auditoría de migración (WP-05 / ADR-004)."""
import uuid

import pytest
from django.core.management import call_command

from apps.core.migration_audit import checksum_registro
from apps.core.models import LegacyMigrationMap
from apps.planificacion.models import Plan
from apps.planificacion.models_v2 import (
    InstrumentoPlanificacion, TipoInstrumento,
)


@pytest.fixture
def plan_legacy(db):
    return Plan.objects.create(
        codigo='PLAN-LEGACY', nombre='Plan legacy', tipo='pei',
        gestion_inicio=2026, gestion_fin=2030,
        fecha_vigencia_desde='2026-01-01',
    )


def test_checksum_estable_ante_mismo_contenido(plan_legacy):
    a = checksum_registro(plan_legacy)
    b = checksum_registro(Plan.objects.get(pk=plan_legacy.pk))
    assert a == b


def test_checksum_cambia_con_el_contenido(plan_legacy):
    antes = checksum_registro(plan_legacy)
    plan_legacy.nombre = 'Nombre modificado'
    plan_legacy.save(update_fields=['nombre', 'updated_at'])
    assert checksum_registro(plan_legacy) != antes


def test_inventario_registra_registros(db, plan_legacy):
    call_command('legacy_audit', '--inventario')
    entrada = LegacyMigrationMap.objects.get(
        app_legacy='planificacion', modelo_legacy='plan',
        uuid_legacy=plan_legacy.pk,
    )
    assert entrada.estado == LegacyMigrationMap.Estados.PENDIENTE
    assert entrada.checksum == checksum_registro(plan_legacy)


def test_inventario_dry_run_no_escribe(db, plan_legacy):
    call_command('legacy_audit', '--inventario', '--dry-run')
    assert not LegacyMigrationMap.objects.exists()


def test_inventario_idempotente(db, plan_legacy):
    call_command('legacy_audit', '--inventario')
    call_command('legacy_audit', '--inventario')
    assert (
        LegacyMigrationMap.objects.filter(
            app_legacy='planificacion', modelo_legacy='plan',
        ).count() == 1
    )


def test_marcar_migrado_requiere_destino(db, plan_legacy):
    from django.core.management.base import CommandError
    with pytest.raises(CommandError):
        call_command(
            'legacy_audit',
            '--marcar-migrado', f'planificacion.Plan:{plan_legacy.pk}',
        )


def test_marcar_migrado_completo(db, plan_legacy):
    tipo = TipoInstrumento.objects.create(
        codigo='PEI-V2', nombre='PEI', nivel='institucional',
    )
    destino = InstrumentoPlanificacion.objects.create(
        tipo=tipo, codigo='PEI-2026', nombre='PEI V2',
        periodo_inicio=2026, periodo_fin=2030,
    )
    call_command(
        'legacy_audit',
        '--inventario',
    )
    call_command(
        'legacy_audit',
        '--marcar-migrado', f'planificacion.Plan:{plan_legacy.pk}',
        '--destino-tipo', 'InstrumentoPlanificacion',
        '--destino-uuid', str(destino.pk),
        '--lote', 'pei-2026',
    )
    entrada = LegacyMigrationMap.objects.get(uuid_legacy=plan_legacy.pk)
    assert entrada.estado == LegacyMigrationMap.Estados.MIGRADO
    assert entrada.tipo_destino == 'InstrumentoPlanificacion'
    assert entrada.uuid_destino == destino.pk
    assert entrada.lote == 'pei-2026'


def test_reconciliar_detecta_discrepancia(db, plan_legacy):
    call_command('legacy_audit', '--inventario')
    entrada = LegacyMigrationMap.objects.get(uuid_legacy=plan_legacy.pk)
    entrada.estado = LegacyMigrationMap.Estados.MIGRADO
    entrada.save(update_fields=['estado', 'fecha'])

    plan_legacy.nombre = 'Manipulado tras migrar'
    plan_legacy.save(update_fields=['nombre', 'updated_at'])

    call_command('legacy_audit', '--reconciliar')
    entrada.refresh_from_db()
    assert entrada.estado == LegacyMigrationMap.Estados.DISCREPANCIA


def test_reconciliar_ok_sin_cambios(db, plan_legacy):
    call_command('legacy_audit', '--inventario')
    entrada = LegacyMigrationMap.objects.get(uuid_legacy=plan_legacy.pk)
    entrada.estado = LegacyMigrationMap.Estados.MIGRADO
    entrada.save(update_fields=['estado', 'fecha'])

    call_command('legacy_audit', '--reconciliar')
    entrada.refresh_from_db()
    assert entrada.estado == LegacyMigrationMap.Estados.RECONCILIADO


def test_reconciliar_dry_run_no_cambia_estado(db, plan_legacy):
    call_command('legacy_audit', '--inventario')
    entrada = LegacyMigrationMap.objects.get(uuid_legacy=plan_legacy.pk)
    entrada.estado = LegacyMigrationMap.Estados.MIGRADO
    entrada.save(update_fields=['estado', 'fecha'])

    call_command('legacy_audit', '--reconciliar', '--dry-run')
    entrada.refresh_from_db()
    assert entrada.estado == LegacyMigrationMap.Estados.MIGRADO


def test_reconciliar_detecta_registro_eliminado(db, plan_legacy):
    call_command('legacy_audit', '--inventario')
    entrada = LegacyMigrationMap.objects.get(uuid_legacy=plan_legacy.pk)
    entrada.estado = LegacyMigrationMap.Estados.MIGRADO
    entrada.save(update_fields=['estado', 'fecha'])

    plan_legacy.delete()
    call_command('legacy_audit', '--reconciliar')
    entrada.refresh_from_db()
    assert entrada.estado == LegacyMigrationMap.Estados.DISCREPANCIA


def test_estado_reporta_conteos(db, plan_legacy):
    call_command('legacy_audit', '--inventario')
    call_command('legacy_audit', '--estado', 'pendiente')
    assert LegacyMigrationMap.objects.filter(
        estado=LegacyMigrationMap.Estados.PENDIENTE,
    ).count() >= 1


def test_registro_unico_por_registro_legacy(db, plan_legacy):
    call_command('legacy_audit', '--inventario')
    call_command('legacy_audit', '--inventario')
    assert LegacyMigrationMap.objects.filter(
        uuid_legacy=plan_legacy.pk,
    ).count() == 1


def test_registro_unico_por_registro_legacy(db, plan_legacy):
    from django.db import IntegrityError
    LegacyMigrationMap.objects.create(
        app_legacy='x', modelo_legacy='y', uuid_legacy=plan_legacy.pk,
        checksum='abc',
    )
    with pytest.raises(IntegrityError):
        LegacyMigrationMap.objects.create(
            app_legacy='x', modelo_legacy='y', uuid_legacy=plan_legacy.pk,
            checksum='def',
        )
