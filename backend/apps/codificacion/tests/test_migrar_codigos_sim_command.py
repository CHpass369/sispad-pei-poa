"""Management-command contracts for SIM-2027 audit and commit."""
import json

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError

from apps.articulacion.models import AccionPOA, ProductoPEI, ResultadoPEI
from apps.codificacion.models import EjecucionMigracionSIM, HomologacionCodigo
from apps.codificacion.services.migracion_sim import MigracionSIMService


@pytest.fixture
def cadena_minima(db):
    resultado = ResultadoPEI.objects.create(
        codigo_resultado='SIM-2027-RI-01',
        denominacion='Resultado',
        cod_entidad='SIM-2027',
        entidad='GAM Sacaba',
        cod_oei='SIM-2027',
        vigencia_desde=2027,
        vigencia_hasta=2030,
    )
    producto = ProductoPEI.objects.create(
        codigo_producto='SIM-2027-PI-01',
        denominacion='Producto',
        resultado_pei=resultado,
    )
    accion = AccionPOA.objects.create(
        codigo_accion='SIM-2027-POA-01',
        denominacion='Acción',
        producto_pei=producto,
        gestion=2027,
    )
    return accion


@pytest.mark.django_db
def test_comando_dry_run_persiste_manifiesto_sin_migrar(cadena_minima, tmp_path):
    manifest_path = tmp_path / 'sim-2027.json'

    call_command(
        'migrar_codigos_sim',
        gestion=2027,
        manifest=str(manifest_path),
    )

    payload = json.loads(manifest_path.read_text(encoding='utf-8'))
    assert payload['resumen']['cambios_planificados'] == 3
    assert EjecucionMigracionSIM.objects.filter(modo='dry_run').count() == 1
    assert HomologacionCodigo.objects.count() == 0
    cadena_minima.refresh_from_db()
    assert cadena_minima.codigo_accion == 'SIM-2027-POA-01'


@pytest.mark.django_db
def test_comando_commit_exige_hash_usuario_y_backup(cadena_minima, tmp_path):
    with pytest.raises(CommandError, match='expected-hash'):
        call_command(
            'migrar_codigos_sim',
            gestion=2027,
            commit=True,
            backup_dir=str(tmp_path),
        )


@pytest.mark.django_db
def test_comando_commit_crea_y_valida_backup_antes_de_escribir(
    cadena_minima, tmp_path, monkeypatch,
):
    usuario = get_user_model().objects.create_user(
        email='responsable@test.gob.bo', password='test123',
    )
    manifest = MigracionSIMService(gestion=2027).construir_manifiesto()
    dump_path = tmp_path / 'pre-commit.dump'
    dump_path.write_bytes(b'validated-dump')
    calls = []

    def fake_backup(*, output_dir, validation_queries):
        calls.append(('backup', AccionPOA.objects.get().codigo_accion))
        return {
            'path': str(dump_path),
            'sha256': 'c' * 64,
            'restore_validated': True,
            'validated_counts': validation_queries,
        }

    monkeypatch.setattr(
        'apps.codificacion.management.commands.migrar_codigos_sim.'
        'PostgresBackupService.create_and_validate',
        fake_backup,
    )

    call_command(
        'migrar_codigos_sim',
        gestion=2027,
        commit=True,
        expected_hash=manifest['manifest_hash'],
        usuario=usuario.email,
        backup_dir=str(tmp_path),
        manifest=str(tmp_path / 'commit.json'),
    )

    cadena_minima.refresh_from_db()
    assert calls == [('backup', 'SIM-2027-POA-01')]
    assert cadena_minima.codigo_accion == '2027.1312.001'
    assert HomologacionCodigo.objects.count() == 3


@pytest.mark.django_db
def test_comando_aborta_si_el_backup_no_puede_validarse(
    cadena_minima, tmp_path, monkeypatch,
):
    usuario = get_user_model().objects.create_user(
        email='responsable-backup@test.gob.bo', password='test123',
    )
    manifest = MigracionSIMService(gestion=2027).construir_manifiesto()

    def failed_backup(**kwargs):
        raise RuntimeError('restore validation failed')

    monkeypatch.setattr(
        'apps.codificacion.management.commands.migrar_codigos_sim.'
        'PostgresBackupService.create_and_validate',
        failed_backup,
    )

    with pytest.raises(CommandError, match='restore validation failed'):
        call_command(
            'migrar_codigos_sim',
            gestion=2027,
            commit=True,
            expected_hash=manifest['manifest_hash'],
            usuario=usuario.email,
            backup_dir=str(tmp_path),
        )

    cadena_minima.refresh_from_db()
    assert cadena_minima.codigo_accion == 'SIM-2027-POA-01'
    assert HomologacionCodigo.objects.count() == 0
